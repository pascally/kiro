from controller import APP
from settings import PORT, HOSTNAME

if __name__ == "__main__":
    APP.run(host=HOSTNAME, port=PORT)
