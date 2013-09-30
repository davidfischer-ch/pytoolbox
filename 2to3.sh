# Sample Python 2 -> 3 conversion of Pyutils
rsync -ah --progress --delete pyutils/ pyutils3/ && 2to3 -x import -w pyutils3
