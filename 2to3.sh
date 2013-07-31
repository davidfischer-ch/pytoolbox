# Sample Python 2 -> 3 conversion of Pyutils
rsync -ah --progress --delete pyutils/ pyutils3/ && 2to3 -w pyutils3
