import os
import requests
from tqdm import tqdm
import signal
import logging

class ModelDownloader:
    def __init__(self, model_name, model_url, model_path, logger):
        self.model_name = model_name
        self.model_url = model_url
        self.model_path = model_path
        self.logger = logger
        self.interrupted = False

    def _handle_interrupt(self, signum, frame):
        self.logger.warning("Download interrupted (signal %s). Cleaning up...", signum)
        self.interrupted = True
        if os.path.exists(self.model_path):
            self.logger.info("Deleting incomplete file: %s", self.model_path)
            os.remove(self.model_path)
        raise KeyboardInterrupt

    def download(self):
        if os.path.exists(self.model_path):
            self.logger.info("Model %s already exists at %s", self.model_name, self.model_path)
            return self.model_path

        self.logger.info("Downloading model %s from %s", self.model_name, self.model_url)
        try:
            signal.signal(signal.SIGINT, self._handle_interrupt)

            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            response = requests.get(self.model_url, stream=True)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            with open(self.model_path, 'wb') as model_file, tqdm(
                total=total_size, unit='B', unit_scale=True, desc=f"Downloading {self.model_name}"
            ) as progress_bar:
                for chunk in response.iter_content(chunk_size=8192):
                    if self.interrupted:
                        break
                    model_file.write(chunk)
                    progress_bar.update(len(chunk))
            if self.interrupted:
                raise KeyboardInterrupt
            self.logger.info("Model downloaded successfully to %s", self.model_path)
        except (Exception, KeyboardInterrupt) as e:
            self.logger.critical("Failed to download the model: %s", e)
            if os.path.exists(self.model_path):
                self.logger.info("Deleting incomplete file: %s", self.model_path)
                os.remove(self.model_path)
            raise
        finally:
            signal.signal(signal.SIGINT, signal.SIG_DFL)
        return self.model_path

if __name__ == "__main__":
    import argparse
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(description="Download a model.")
    parser.add_argument("--model_name", required=True, help="Name of the model to download.")
    parser.add_argument("--model_url", required=True, help="URL of the model.")
    parser.add_argument("--model_path", required=True, help="Path to save the downloaded model.")
    args = parser.parse_args()

    downloader = ModelDownloader(args.model_name, args.model_url, args.model_path, logger)
    try:
        downloader.download()
    except Exception as e:
        logger.error("Error during model download: %s", e)
