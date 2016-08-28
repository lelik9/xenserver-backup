# coding=utf-8
from app.logger import logger
from app import app


if __name__ == '__main__':
    app.LOGGER = logger
    app.run(debug=True, host='0.0.0.0', port=5001)
