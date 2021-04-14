import sys

print(sys.argv)
if sys.argv[1] == "headless":
    headless = True
local_host = sys.argv[2]