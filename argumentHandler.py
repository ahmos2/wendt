parser = ArgumentParser()
parser.add_argument("--remotescheme", default="https")
parser.add_argument("--remotehost", default="128.39.165.228")
parser.add_argument("--remoteport", default="8080")

parser.add_argument("--input", help="Ingoing canbus to sensor", default="vcan0")
parser.add_argument("--output", help="Outgoing canbus to network", default="vcan0")

parser.add_argument("--company", type=int, default=0)
parser.add_argument("--ship", type=int, default=0)
parser.add_argument("--controller", type=int, default=0)
parser.add_argument("--instance", type=int, default=0)

parser.add_argument("--nodeid", type=int, default=99)

parser.add_argument("--privatekey", default="Never gonna give you up")
parser.add_argument("--signature", default="Never gonna let you down")
parser.add_argument("--username", default="remote")
parser.add_argument("--password", default="remote")

parser.add_argument("--verbose", action="store_true")
config=parser.parse_args()