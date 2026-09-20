import utils.logging_config as logging_config
from services import learn_service


def main():
    learn_service.learn()



if __name__ == "__main__":
    logging_config.setup_logger()
    main()
