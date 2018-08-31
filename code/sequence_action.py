from action import action
import collections

class sequence_action(action):
  """
    An action for calling multiple actions, one at a time.
  """

  def __init__(self):
    self.actions = collections.deque()

  def update(self, dt):
    # Get the first action out of the deque
    front = self.actions[0]

    while True:

      # Check if the first action is over
      if front.is_over():

        # End the action, and pop it off the deque
        # We pop it first because if end adds a new action to the deque, we
        # need to start that new action (see add_action for more information)
        self.actions.popleft()
        front.end()

        # If we have no more actions left, then we are done
        if len(self.actions) == 0:
          return None

        # Get the next action from the front of the deque, and start it. We'll
        # fall back through to the start of the while loop from here.
        front = self.actions[0]
        front.start()
      else:

        # The action wasn't over, so let's update it.
        front.update(dt)

        # Now we check again to see if the action is over
        if front.is_over():

          # End the action, and pop it off the deque
          # We pop it first because if end adds a new action to the deque, we
          # need to start that new action (see add_action for more information)
          self.actions.popleft()
          front.end()

          # If we have no more actiosn left, then we are done
          if len(self.actions) == 0:
            return None

          # Get the next action from the front of the deque, and start it.
          # We'll fall back through to the start of the while loop from here.
          front = self.actions[0]
          front.start()
        else:

          # The action updated, but isn't done yet. We're done updating the
          # list.
          return None

  def is_over(self):
    # We're over when there are no more actions to run
    return len(self.actions) == 0

  def add_action(self, action):
    # Append the action to the end of the sequence
    self.actions.append(action)

    # If we have 1 action in the deque at this point, our new action will start
    # running immediately n the next update. Let's start it now.
    # This is why we pop the first element out of the deque before ending the
    # action - if we ended the action first, and the end method for that action
    # added a new action to this list, the first action would still be in the
    # deque at this point.
    if len(self.actions) == 1:
      self.action.start()
