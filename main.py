import sys
import logging
from agents import process_blood_test_report, read_pdf

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    if len(sys.argv) < 2:
        logger.error("Usage: python main.py <path_to_pdf_file>")
        return

    pdf_path = sys.argv[1]
    try:
        logger.info(f"Starting to read PDF: {pdf_path}")
        blood_test_report = read_pdf(pdf_path)
        
        if not blood_test_report:
            logger.error("Could not extract text from the PDF. Please ensure it's a valid blood test report.")
            return

        logger.info("PDF read successfully. Starting to process blood test report...")
        result = process_blood_test_report(blood_test_report)

        if result:
            logger.info("Analysis completed successfully")
            print("Analysis Result:")
            print(result)
        else:
            logger.error("Could not process the blood test report")

    except Exception as e:
        logger.exception(f"An error occurred: {e}")

if __name__ == "__main__":
    main()