class bomb:
  def __init__(self):
    self.__message = ''

  def get_message(self):
    return self.__message

  def set_message(self, val):
    self.__message = val
    print(f'Bomb says: {self.__message}')

  message = property(get_message, set_message)
