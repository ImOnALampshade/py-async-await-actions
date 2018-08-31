from action import action

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
