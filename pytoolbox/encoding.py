__all__ = ['csv_reader', 'to_unicode']


def to_unicode(message, encoding='utf-8'):
    if isinstance(message, str):
        return message
    if hasattr(message, 'decode'):
        return message.decode(encoding)
    return str(message)


def csv_reader(path, delimiter=';', quotechar='"', encoding='utf-8'):
    """Yield the content of a CSV file."""
    with open(path, 'r', encoding) as f:
        for line in f.readlines():
            line = line.strip()
            yield [cell for cell in line.split(delimiter)]
    # import csv
    # reader = csv.reader(f, delimiter=delimiter, quotechar=quotechar)
    # for row in reader:
    #    yield [cell for cell in row]
    #    # yield [text_type(cell, 'utf-8').encode('utf-8') for cell in row]
