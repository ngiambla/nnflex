''' pipeline.py

'''

class Stage(object):
    ''' Stage:

    A Stage in a pipeline.
    Exposes the necessary state that can be shared when passing
    information from stage to stage.

    Args:
        message: a Message object.

    Returns:
        a Stage object.

    '''
    def __init__(self):
        self._message = None
        
    def process(self):
        raise NotImplementedError("Specialize to the specification of the Accelerator and Device.")


    def get_message(self):
        return self._message

    def accept_message(self, message):
        self._message = message