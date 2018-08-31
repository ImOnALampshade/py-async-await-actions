class action:
  def start(self):
    """
      Called when the action is started. When an action is re-used, this should
      reset its state to its original value.
    """
    pass

  def update(self, dt):
    """
      Called once per frame to update this action. Will only ever be called
      after start, and before end. If an action is re-used, start will be
      called again before update is called.
    """
    pass

  def end(self):
    """
      Called when this action is ended. Will only be called after is_over
      returns True. If an action is ended pre-maturely, this will not be
      called.
    """
    pass

  def is_over(self):
    """
      Checks if this action has ended. Should return a truthy value when the
      action is over, and falsey when the action should continue.
    """
    return True

  def result(self):
    """
      Gets the result of this action, if it is doing something in the
      background that should be returned to the caller.
    """
    return None
