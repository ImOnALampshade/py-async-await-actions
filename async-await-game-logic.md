# Leveraging async/await for game logic

I've been experimenting with using async/await to write game logic code in Python. Because I've only used Python to do this, this entire post will be using Python for example code and implementation details. This code could also be adapted to run in JavaScript, and probably even in C# if you're extremely adventurous.

# Goals

The goal of this post is to show you how to take messy game logic code, like this:

```python
def script(self):
  for i in range(0, 5):
    cb_act = callback_action(lambda: self.bomb.message = f'{5 - i}...')
    self.action_list.add_action(cb_act)

    beep_act = callback_action(self.bomb.beep)
    self.action_list.add_action(beep_act)

    wait_act = wait_action(1)
    self.action_list.add_action(wait_act)

    def defused_callback():
      if self.bomb.defused:
        self.action_list.clear()
    defused_act = callback_action(defused_callback)
    self.action_list.add_action(defused_act)

  exp_act = callback_action(self.bomb.explode)
  self.action_list.add_action(exp_act)
```

And turn it into something more high level, cleaner, and more flexible, like this:

```python
async def script(self):
  for i in range(0, 5):
    self.bomb.message = f'{i}...'
    self.bomb.beep()
    await self.wait(1)

    if self.bomb.defused:
      return None

  self.bomb.explode()
```

# Actions lists: what they solve, and the problems they have

First, let's look at how to make an in-game timer for a bomb, with a small LCD timer on it which will count down from 5, and then explode. Let's take a look at our script:


```python
def script(self):
  for i in range(0, 5):
    self.bomb.message = f'{5 - i}...'
    self.wait(1)

  self.bomb.explode()
```

This is a pretty straight forward script - however, it's not as simple as the script just running over those 5 seconds. This entire script runs within the update loop for one frame (The frame when the countdown timer was triggered), and we have to do other things in the game, like rendering, responding to player input, and sending hoards of enemies after the player.

Since each frame runs in 1/60th of a second, how can we have this script perform actions over multiple frames when it runs entirely inside of one frame?

## Enter: Actions

An "action" is something we can use in our games to run logic over multiple frames, which can have some logic toward how they run. We add these actions to a queue - an action list - which will iterate through these actions, running one at a time.

Let's take a look at our base action class:

```python
class action:
  def start(self): pass
  def update(self, dt): pass
  def end(self): pass
  def is_over(self): return True
  def result(self): return None
```

Our action has 4 methods, which are pretty straightforward:

* `start`: Called when the action is first started
* `update`: Called every frame the action is running for
* `end`: Called when the action has ended
* `is_over`: Called every frame to check if the action is over
* `result`: Gets the result of the action, for when an action is doing some other work in the background we want to get back.

Actions are placed into a queue, called an action list. When you add an action to the list, it gets placed at the end of the queue. As the game updates, we grab the first action in the queue, and update it. When it ends, we pop the front of the queue, and move onto the next action. You can see the implementation in the code files.

We can define actions to do whatever we want in the game - and their logic can span multiple frames, so we can have our bomb countdown script made using these actions. Let's create two actions, which we'll use for our bomb. `wait_action` and `callback_action`.

`wait_action` will wait some number of seconds, and then finish. This will block the action list from continuing for as long as we want.

```python
class wait_action(action):
  """
    An action that will do nothing, and block the action list, until a timer is
    completed
  """
  def __init__(self, time):
    self.current_time, self.end_time = 0, end_time

  def start(self):
    # We re-set current_time to 0 here in case this action object is being
    # re-used
    self.current_time = 0

  def update(self, dt):
    # Update the current time
    self.current_time += dt

  def is_over(self):
    # We're done when our current time has gone past the end time
    return self.current_time >= self.end_time
```

`callback_action` will immediately call it's callback function, and the end right away. By using closures in Python, we can use this to inject any function call we want into an action list.

```python
class callback_action(action):
  """
    An action that will simply call a function and end immediately
  """
  def __init__(self, callback):
    """
      Initializes a new callback action

      callback:
        The callback we want to call when this action starts
    """
    self.callback = callback

  def start(self):
    # Just call our callback
    self.callback()

  def is_over(self):
    # We end immediately, because we only need to run the start method
    return True
```

With our new actions, let's update our script to work within our main game loop:

```python
def script(self):
  for i in range(0, 5):
    cb_act = callback_action(lambda: self.bomb.message = f'{5 - i}...')
    self.action_list.add_action(cb_act)

    wait_act = wait_action(1)
    self.action_list.add_action(wait_act)

  exp_act = callback_action(self.bomb.explode)
  self.action_list.add_action(exp_act)
```

So now that we are appending an action to an action list when these functions are called, our script works without having to be run across multiple frames. Our script just queues up multiple things for our bomb to do, and the action list will iterate through this list until it runs out of actions.

While this solves our problems with the bomb, it isn't the best system we can use.

## Issue 1 - Loops

Consider what would happen if instead of our bomb counting down from 5, we started it at a much higher number - say, 5 minutes (or 300 seconds). In our script, this is an easy change:

```python
def script(self):
  for i in range(0, 300):
    cb_act = callback_action(lambda: self.bomb.message = f'{300 - i}...')
    self.action_list.add_action(cb_act)

    wait_act = wait_action(1)
    self.action_list.add_action(wait_act)

  exp_act = callback_action(self.bomb.explode)
  self.action_list.add_action(exp_act)
```

However, there's a couple problems here:

* We are creating 601 actions - 300 set_text actions, 300 wait_actions, and 1 explode action - in a single frame. Python's memory allocator will not be very happy here.
* We are using a lot of memory, for something very simple.

To make matters worse, let's say we are creating a script for a flickering light - at some random time between 10 and 20 seconds, a light will turn off for 0.25 seconds, and then turn back on. How would we implement that? We may naively try to do this right off the bat (assuming that all our methods will simply add an action to the action list):

```python
def script(self):
  while True:
    time = random.uniform(10, 20)

    wait1 = wait_act(time)
    self.action_list.add_action(wait1)

    light_off = callback_action(self.light_off)
    self.action_list.add_action(light_off)

    wait2 = wait_act(0.25)
    self.action_list.add_action(wait2)

    light_on = callback_action(self.light_on)
    self.action_list.add_action(light_on)
```

However, the issue here is clear: Once our script starts, it will never end. We will be stuck in an infinite loop, adding more and more actions to the list until our computer can't take it anymore, and we run out of memory for our action list.

## Issue 2 - Non-actions

Our bomb has a big issue - it doesn't beep. Because bombs should beep (for dramatic effect), we now need to add in some beeps.

So now, we update our script to:

```python
def script(self):
  for i in range(0, 5):
    cb_act = callback_action(lambda: self.bomb.message = f'{5 - i}...')
    self.action_list.add_action(cb_act)

    # Beep here, after updating the message!
    self.bomb.beep()

    wait_act = wait_action(1)
    self.action_list.add_action(wait_act)

  exp_act = callback_action(self.bomb.explode)
  self.action_list.add_action(exp_act)
```

We go to run the script, and instead of beeps after every second, we hear 5 overlapping beeps followed by the timer starting. Can you tell why? Our beep method isn't called by a callback action - which means that when the script runs, and is queuing up all the actions, it will beep in the middle of it's queue. Let's fix this:

```python
def script(self):
  for i in range(0, 5):
    cb_act = callback_action(lambda: self.bomb.message = f'{5 - i}...')
    self.action_list.add_action(cb_act)

    beep_act = callback_action(self.bomb.beep)
    self.action_list.add_action(beep_act)

    wait_act = wait_action(1)
    self.action_list.add_action(wait_act)

  exp_act = callback_action(self.bomb.explode)
  self.action_list.add_action(exp_act)
```


While this mistake is entirely avoidable, it does make these scripts more difficult to write - you constantly have to be adding callback actions to do simple things, because otherwise, things will not happen when you intend them to.

## Issue 3 - Responding to changes between actions

What if our bomb is defused before the timer hits 0?

A naive approach would look something like this:

```python
def script(self):
  for i in range(0, 5):
    cb_act = callback_action(lambda: self.bomb.message = f'{5 - i}...')
    self.action_list.add_action(cb_act)

    beep_act = callback_action(self.bomb.beep)
    self.action_list.add_action(beep_act)

    wait_act = wait_action(1)
    self.action_list.add_action(wait_act)

    if self.bomb.defused:
      return None

  exp_act = callback_action(self.bomb.explode)
  self.action_list.add_action(exp_act)
```

However, this won't work, because of the same issue we had with the beeping earlier. Because the defused flag will (probably) start as `False`, and our script does not run across all the frames the bomb is ticking down during, we will only check the defused flag once (Well, 5 times back-to-back) - the frame that the script runs.

Instead, we need to use callback action again, to do this:

```python
def script(self):
  for i in range(0, 5):
    cb_act = callback_action(lambda: self.bomb.message = f'{5 - i}...')
    self.action_list.add_action(cb_act)

    beep_act = callback_action(self.bomb.beep)
    self.action_list.add_action(beep_act)

    wait_act = wait_action(1)
    self.action_list.add_action(wait_act)

    def defused_callback():
      if self.bomb.defused:
        self.action_list.clear()
    defused_act = callback_action(defused_callback)
    self.action_list.add_action(defused_act)

  exp_act = callback_action(self.bomb.explode)
  self.action_list.add_action(exp_act)
```

This still isn't a perfect solution - because we just nuke our action list when the bomb is defused, any non-related actions in the queue for the bomb will never get run. And, of course, it's just as annoying as when we had to deal with the beeping.

## What is wrong with all of these?

Well, not all that much is wrong here. We have to rely pretty heavily on callback_action to do a lot of what we'd want to do here, but we can make it work.

The problem is that is isn't that simple. Let's look at this code, which would not at all work given our current implementation, but is remarkably simple:

```python
def script(self):
  for i in range(0, 5):
    self.bomb.message = f'{i}...'
    self.bomb.beep()
    self.wait(1)

    if self.bomb.defused:
      return None

  self.bomb.explode()
```

Now let's look at our finished code:

```python
def script(self):
  for i in range(0, 5):
    cb_act = callback_action(lambda: self.bomb.message = f'{5 - i}...')
    self.action_list.add_action(cb_act)

    beep_act = callback_action(self.bomb.beep)
    self.action_list.add_action(beep_act)

    wait_act = wait_action(1)
    self.action_list.add_action(wait_act)

    def defused_callback():
      if self.bomb.defused:
        self.action_list.clear()
    defused_act = callback_action(defused_callback)
    self.action_list.add_action(defused_act)

  exp_act = callback_action(self.bomb.explode)
  self.action_list.add_action(exp_act)
```

It's easy to tell which one is more intuitive, cleaner, and easier to write. However, how would we be able to write code like the first example?

# Enter: Async/await

**NOTE: I'm glossing over this topic quite a bit to get you understand the internals of async code, in order to implement your own asynchronous event loop. There is a lot of hand waving for the sake of brevity. Please do not take this as gospel.**

Typically, async/await is used to create non-blocking IO for things like network access and disk reads/writes. The idea behind it is that while you are waiting to get data back from a server, or waiting for a file read operation to finish, you can still continue doing useful work. This is particularly useful for things like webservers - where you need to respond to hundreds of requests per second while waiting for things like file read operations, remote database access, etc. You still want to be able to respond to other requests while you are running a database query to respond to another request, so you can use async to "suspend" the first request until you finish with your work, and continue responding to other request in the meantime.

The traditional approach to this has been multi-threading, but that adds a lot of complexity which, it turns out, is not necessary. With asynchronous code, we can easily do this all from one thread! Using async and await is one approach to doing this, but it is the easiest and what you are most likely to encounter going forward.

## What async isn't

Async is not multi-threading. In fact, most of the time, asynchronous code refers to code that runs in only one thread.

## asyncio

The typical way that we use async in Python to do disk and network IO is through the `asyncio` module. Here is an example where we can read a file and print its contents (Because python does not support async file IO out of the box, this example requires `aiofiles` on your machine, [see the repo](https://github.com/Tinche/aiofiles) for installation instructions):

```python
import aiofiles
import asyncio

async def print_file(f):
  contents = await f.read()
  print(contents)

async def main():
  async with aiofiles.open('example.txt', 'rt') as f:
    await print_file(f)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
```

So how does this work?

Let's start with these 3 lines:

```python
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
```

Our `print_file` and `main` functions are relatively straightforward - the only weirdness they have compared to "normal" python is a sprinkling of the `async` and `await` keywords.

Our declarations for `print_file` and `main` start with `async` - this is so that Python knows that these functions run asynchronously, which allows us to use `await` inside of them. We'll talk more about this later.

`await` is the secret sauce in all of this. In our `print_file` function, we could do what we typically do in python by just calling `read` like normal:

```python
contents = f.read()
print(contents)
```

However, as we all know, hard drive access is a very slow operation. Reading the entire contents of our file into memory is going to take at least a few milliseconds - precious clock cycles that could be spent bitcoin mining. So, we could just do something else while we wait for it to finish - and this is where `await` comes in.

In `aiofiles`, `f.read()` doesn't return a string with the file contents. Instead, it returns a promise - a promise that says that "in the future, this be available." When we say `await f.read()`, we are adding that promise to the event loop, and then letting that file read finish while we do more work. You can await any promise, and get the resulting value from that promise, by using `await [promise]`, where `promise` is typically a function call.

Because our `print_file` function is marked as `async`, it will return a promise - which means that, in order to actually run this function, it must be `await`ed. However, you can only `await` from an `async` function. Because `main` is also `async`, it can await `print_file`.

However, code written at the global level in python is not `async`. So, how can we await `main`? We have to use an event loop object from `asyncio`. I won't go into much detail about this, because we aren't to concerned with how `asyncio` works for the purposes of this post.

## Without asyncio

`asyncio` is a great module, and one that I highly recommend learning if you've got Python on your resume. However, we aren't interested in using `async` for file or network IO - we want to use it for game logic. So, let's look at how our


