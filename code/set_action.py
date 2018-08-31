from action import action

def check_continue_and_end(action):
  """
    Checks if an action should continue, and if it should not, ends the action

    action:
      The action to check

    return:
      False when the action is over
      True when the action should continue
  """
  if action.is_over():
    action.end()
    return False
  else:
    return True

class set_action(action):
  """
    An action for calling multiple actions, all in parallel.
  """
  def __init__(self):
    self.actions = []
    self.started = False

  def start(self):
    # Start all the actions
    for action in self.actions:
      action.start()

    # Now that we've iterated through the whole list and started all the
    # actions, if another action is added, it won't be started. So we set the
    # started flag so that add_action knows to start the action as soon as it
    # is added.
    self.started = True

  def update(self, dt):
    # Filter out our actions to not include actions that are over.
    # check_continue_and_end will check if an action is over for us, and end it
    # if it is over.
    self.actions = filter(check_continue_and_end, self.actions)

    # Loop over all the actions still in our list and update them.
    for action in self.actions:
      action.update(dt)

  def is_over(self):
    # We are done when there are no more actions left
    return len(self.actions) == 0

  def add_action(self, action):
    self.actions.append(action)

    # If start has already been called on this action, we should start the new
    # one now, otherwise start will not be called anywhere else.
    if self.started:
      action.start()
