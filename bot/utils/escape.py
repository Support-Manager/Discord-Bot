def escaped(msg: str):
    """ Escaping code blocks and double line breaks. """
    return msg.replace("`", "'").replace("\n\n", " ")
