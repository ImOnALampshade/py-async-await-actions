import sequence_action

class action_list:
  def __init__(self):
    # We're just going to re-use the logic from sequence_action here, because
    # it already implements what we want.
    # sequence_action doesn't need a start or end method, only update.
    self.sequence = sequence_action.sequence_action()

  def update(self, dt):
    # Check if the sequence is over, and if it isn't, we'll update it.
    if not self.sequence.is_over():
      self.sequence.update()

  def add_action(self, action):
    # Add the action to our sequence
    self.sequence.add_action(action)
