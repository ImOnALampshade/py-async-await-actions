# Leveraging async/await for game logic

I've been experimenting with using async/await to write game logic code in Python. Because I've only used Python to do this, this entire post will be using Python for example code and implementation details. This code could also be adapted to run in JavaScript, and probably even in C# if you're adventurous.

# Actions lists: what they solve, and the problems they have

Consider this Python script, in the context of a game:

```python
def script(self):
  self.move_forward(3)
  self.turn(90)
  self.move_forward(3)
```

Our intention here is for our character to move forward 3 spaces, turn 90 degrees, then move forward 3 spaces in the new direction they are facing. However, how does this function work? We know that this script must be called from somewhere within the update loop of the game, and we also know that the character moving forward must take place over multiple frames, so that we can play some fancy animations and all that while the player moves forward.

Say it takes 1 second to move forward 3 spaces, and 0.5 seconds to turn 90 degrees. This means that in order to execute this entire script, we need 2.5 seconds (Which is 150 frames at 60 FPS). So, how can we use this script inside the update of 1 frame, when it takes 150 frames to finish the script?

## Enter: Actions

An "action" is something we can use in our games to run logic over multiple frames, which can have some logic toward how they run.

Let's take a look at a simple action:

```python
class action:
  def start(self): pass
  def update(self, dt): pass
  def end(self): pass
  def is_over(self): return True
```

Our action has 4 methods, which are pretty straightforward:

* `start`: Called when the action is first started
* `update`: Called every frame the action is running for
* `end`: Called when the action has ended
* `is_over`: Called every frame to check if the action is over

Let's take a look at a couple of action implementations, so we can understand how these work:

```python
class wait_action(action):
  """
    An action that just blocks for some period of time
  """
  def __init__(self, time):
    self.time = time

  def update(self, dt):
    self.time -= dt

  def is_over(self):
    return self.time <= 0

class animation_action(action):
  """
    An action that starts playing an animation, and blocks until it finishes
  """
  def __init__(self, animationComponent, animationName):
    self.animationComponent = animationComponent
    self.animationName = animationName

  def start(self):
    self.animationComponent.set_animation(self.animationName)

  def is_over(self):
    self.animationComponent.has_animation_ended()
```

We can define actions to do whatever we want in the game - and their logic can span multiple frames, so we can have our script like we had above!

With our new actions, let's look at what the `move_forward` and `turn` actions look like:

```python
def move_forward(self, spaces, actionList=self):
  act = walk_action(spaces)
  actionList.add_action(act)

def turn(self, degrees, actionList=self):
  act = turn_action(degrees)
  actionList.add_action(act)
```

So we can see that we are appending an action to an action list when these functions are called - which makes our script work without having to be run across multiple frames. Our script just queues up multiple things for our character to do, and the action list will iterate through this list until it runs out of actions.

However, there are still some big issues with this code that make it difficult to use.

## Issue 1 - Loops

Consider what would happen if we were to do the following, in order to continually repeat the script we have written to make the character walk around in a circle (Or, I guess a square):

```python
def script(self):
  while True:
    self.move_forward(3)
    self.turn(90)
```

Using `while True` makes this function repeat forever, and keep adding more actions - which is our intention. However, this script is still running inside the main game loop - and the main game loop will never resume after this. This function will just loop infinitely, appending more and more action objects to the end of a list, eating up all the memory while the game is hard locked.

There's a few solutions to this. Let's create a new type, `loop_action`, in order to create a loop for actions to repeat (Implementation of this action is left as an exercise to the reader).

Now, we can use a `loop_action` to create our loop:

```python
def script(self):
  loop = loop_action(condition=lambda True)

  # Now we pass the loop into move_forward and turn, so that the actions are
  # added to that action list instead of our object's action list
  self.move_forward(3, loop)
  self.turn(90, loop)

  # Add the action to our action list
  self.add_action(loop)
```

So, while we can still create loops - they aren't as easy, and don't fit into our typical experience of programming. We can't just create a `for` or `while` loop like we may typically want to, but instead, we must use a new action type to stand in for these.

We also have the issue that all our actions must be re-runnable in order to be added to a loop - that is, after the action ends, if it is started again, it must be able to reproduce the same effects it had before. This is something we will have to keep in mind when writing all our actions going forward! (Note that the `wait_action` defined above would not work under this system)

## Issue 2 - Non-actions

Let's say we create a new function which does **not** use an action in the background, called `take_damage`:

```python
def take_damage(self, amount):
  self.health -= amount
```

Now, let's modify our original script to make the character take 30 damage when they finish the script:

```python
def script(self):
  self.move_forward(3)
  self.turn(90)
  self.move_forward(3)

  self.take_damage(30)
```

So, when does the character take damage? Our intention here is for the character to take damage after moving, turning, and moving again - however, because `take_damage` applied immediately, and `move_forard` and `turn` queue up actions to be performed later, `take_damage` will be applied immediately when `script` is called.

We can also solve this, by creating a new action, which we will call `callback_action`. Now we can use this action to call `take_damage` as part of the action list:

```python
def script(self):
  self.moveForward(3)
  self.turn(90)
  self.moveForward(3)

  dmg_act = callback_action(lambda: self.take_damage(30))
  self.add_action(dmg_act)
```

This works - but it might leave an uninformed reader confused as to why we only use `callback_action` for `take_damage`, and not `move_forward` or `turn`. Which becomes doubly confusing when you realize that `move_forward` and `turn` would probably still work when wrapped in a `callback_action`!

## Issue 3 - Responding to changes between actions

Now that our character is taking damage, they probably want to heal if their health is low. But how do we let them make that decision? Typically, we could use in `if` statement to accomplish this easily, but that won't work with our script. Consider this:

```python
def script(self):
  self.moveForward(3)
  self.turn(90)
  self.moveForward(3)
  self.callbackAction(lambda: self.takeDamage(30))
  if self.health < 50:
    self.heal()
```

This is essentially the same problem as earlier: We have to call heal as part of the action list. But that's fine, we can define a new `conditional_action` that will only call an action if a condition is met:

```python
def script(self):
  self.moveForward(3)
  self.turn(90)
  self.moveForward(3)

  dmg_act = callback_action(lambda: self.take_damage(30))
  self.add_action(dmg_act)

  heal_act = conditional_action(
    (lambda: self.health < 50),
    callback_action(lambda: self.heal())
  )
  self.add_action(heal_act)
```

So now we can use `conditional_action` in place of all our if statements. We can expand this action to allow us to build complicated if/else structures in our actions if we want to, as well.

## What is wrong with all of these?

So what have we done with these actions? Let's apply all of our scripts together into one:

```python
def script(self):
  loop = loop_action(condition=lambda: True)
  self.move_forward(3, loop)
  self.turn(90, loop)

  dmg_act = callback_action(lambda: self.take_damage(30))
  loop.add_action(dmg_act)

  heal_act = conditional_action(
    (lambda: self.health < 50),
    callback_action(lambda: self.heal())
  )
  loop.add_action(heal_act)

  self.add_action(loop)
```

While this code will work for our purposes, it isn't very easy to understand right off the bat. It doesn't mesh very well with the code we typically write.

Let's take a step back - and let's look at what this could would look like if we wrote it in a more "typical" way:

```python
def script(self):
  while True:
    self.moveForward(3)
    self.turn(90)

    self.takeDamage(30)

    if self.health < 50:
      self.heal()
```

Basically, all we've done by defining all these actions is just created our own embedded programming language (Complete with while loops, if statements, and function calls) using action lists! We've taken our already Turing complete language of Python, and we're trying to create some new Turing complete data structure inside of it.

Why, though? We haven't made it easier to program - in fact, just the opposite! Our goal is to approach something like the turtle code we looked at when we started, using while loops and if statements just like we do in the rest of the language.

# Enter: Async/await

Typically, async/await is used to create non-blocking IO for things like network access and disk reads/writes. The idea behind it is that while you are waiting to get data back from a server, or waiting for a file read operation to finish, you can still continue doing useful work. This is particularly useful for things like webservers - where you need to respond to hundreds of requests per second while waiting for things like file read operations, remote database access, etc. You still want to be able to respond to other requests while you are running a database query to respond to another request.

However, many high level languages - Like Python, and JavaScript - support async/await in such a generic way that we can actually leverage it to do whatever we want!
