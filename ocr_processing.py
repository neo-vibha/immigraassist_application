import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import logging
import re
from PIL import Image, ImageEnhance
import numpy as np
import cv2
import os
from sklearn.metrics.pairwise import cosine_similarity
from docx import Document
from sentence_transformers import SentenceTransformer
from thefuzz import fuzz


pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess(text):
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)  # normalize whitespace
    text = re.sub(r'[^\w\s]', '', text)  # remove punctuation
    return text.strip()


def compare(field, form_value, db_value):   # extracted, form
    flag = None
    if field == "education":
        form_value = preprocess(form_value)
        db_value = preprocess(db_value)
        similarity = fuzz.token_set_ratio(form_value, db_value)
        print(f"Cleaned doc similarity: {similarity}%")
        if similarity>85:
            dict_final = True
            flag = True
        else:
            dict_final = {field:False,'extracted_data': form_value, 'form_from_Db': db_value,
                          'field':"Educational Qualification", "html_field":field}
            flag = False
    else:
        if str(form_value).strip().lower() == str(db_value).strip().lower():
            dict_final = True
            flag = True
        else:
            if field == "fein_number":
                html_content = "Federal Employer Identification Number (FEIN)"
            elif field == "lca_number":
                html_content = "LCA or ETA Case Number"
            elif field == "passport_expiry_data":
                html_content = "Passport Expiry Date"
            elif field == "job_title":
                html_content = "Job Title"
            elif field == "passport_number":
                html_content ="Passport Number"

            dict_final = {'field':False,'extracted_data': form_value, 'form_from_Db': db_value,
                          'field':html_content,"html_field":field}
            flag = False
    return dict_final, flag


def extract_text_from_word(word_path):
    # Open the Word document
    doc = Document(word_path)
    
    # Extract text from the Word document
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    
    return text

def extract_text_from_file(filepath):
    """Extract text from PDF or image using OCR."""
    try:
        if filepath.endswith('.pdf'):
            images = convert_from_path(filepath, 500, poppler_path=r'C:\poppler-24.08.0\Library\bin')
            text = ""
            for image in images:
                image = image.convert('L')
                text += pytesseract.image_to_string(image)
            return text
        elif filepath.endswith(('.png', '.jpg', '.jpeg')):
            # image = Image.open(filepath)
            image = Image.open(filepath).convert('L')
            return pytesseract.image_to_string(image)
        else:
            return "Unsupported file format"
    except Exception as e:
        logging.error(f"OCR extraction failed: {e}")
        return ""
    
def extract_text_from_certificate(filepath):
    """Extract text from PDF or image using OCR."""
    try:
        if filepath.endswith('.pdf'):
            images = convert_from_path(os.path.join(os.getcwd(), filepath), 500, poppler_path=r'C:\poppler-24.08.0\Library\bin')
            image_np = np.array(images[0])
            # Step 1: Convert the image to grayscale
            gray_image = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
            _, threshold_image = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Step 3: Denoising (Remove noise from the image to make text clearer)
            denoised_image = cv2.fastNlMeansDenoising(threshold_image, None, 30, 7, 21)

            # Step 4: Enhance the contrast of the image
            enhanced_image = Image.fromarray(denoised_image)
            enhanced_image = ImageEnhance.Contrast(enhanced_image).enhance(2)

            text = ""
            for image in images:
                text += pytesseract.image_to_string(enhanced_image)
            return text
        elif filepath.endswith(('.png', '.jpg', '.jpeg')):
            image = Image.open(filepath)
            return pytesseract.image_to_string(image)
        else:
            return "Unsupported file format"
    except Exception as e:
        logging.error(f"OCR extraction failed: {e}")
        return ""
    

def extract_structured_data(text):
    data = {}

    def find(pattern, default=""):
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else default

    data["full_name"] = find(r"Full Name.*?:\s*(.+)")
    data["birthdate"] = find(r"Male\s+Female\s*\n(\d{2}-\d{2}-\d{4})", "")
    data["gender"] = ""  # OCR cannot detect filled circle
    data["nationality"] = find(r"Nationality\s*\n(.+)")
    data["marital_status"] = find(r"Marital Status\s*\n(.+)")
    data["passport_number"] = find(r"Passport Number\s*\*?\s*\n(\d+)")
    data["passport_issuance_country"] = find(r"Issuance Country\s*:?\s*\*?\s*\n?([A-Za-z ]+)")
    data["passport_issue_date"] = find(r"Date of Issue\s*\n(\d{2}-\d{2}-\d{4})")
    data["passport_expiry_date"] = find(r"Date of Expiry\s*\n(\d{2}-\d{2}-\d{4})")

    data["travel_purpose"] = find(r"Purpose of Travel.*?:\s*(.+)")
    data["arrival_date"] = find(r"Date of Arrival.*?:\s*(\d{2}-\d{2}-\d{4})")
    data["us_address"] = find(r"U\.S\. Address:\s*(.+)")

    data["has_been_to_us"] = find(r"been to the U\.S\.\?:\s*(Yes|No)")
    data["previous_visa_type"] = find(r"Previous U\.S\. Visa Type:\s*(.+)")
    data["last_us_visit_date"] = find(r"Date of Last U\.S\. Visit:\s*(.+)")
    data["visa_refusal_details"] = find(r"Details of Visa Refusals:\s*(.+)")

    data["father_name"] = find(r"Father[’']s Full Name:\s*(.+)")
    data["father_nationality"] = find(r"Father[’']s Nationality:\s*(.+)")
    data["mother_name"] = find(r"Mother[’']s Full Name:\s*(.+)")
    data["mother_nationality"] = find(r"Mother[’']s Nationality:\s*(.+)")

    data["job_title"] = find(r"Job Title:\s*(.+)")
    data["employer_name"] = find(r"Employer Name:\s*(.+)")
    data["employer_address"] = find(r"Employer Address:\s*(.+)")
    data["employment_dates"] = find(r"Employment Dates:\s*(.+)")

    data["university_name"] = find(r"University Name:\s*(.+)")
    data["degree"] = find(r"Degree:\s*(.+)")

    data["has_criminal_record"] = find(r"arrested.*crime.*?:\s*(No|Yes)", "")
    data["has_health_conditions"] = find(r"health conditions[^\n]*\?:\s*(No|Yes)", "")
    data["has_contagious_diseases"] = find(r"contagious diseases[^\n]*\?:\s*(None|No|Yes|.+)", "")

    return data

def extract_passport_data_(text):
    print("======= OCR PASSPORT TEXT START =======")
    print(text)
    print("======= OCR PASSPORT TEXT END ========")

    def find(pattern, default=""):
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match and match.groups() else default

    def format_date(yyMMdd):
        try:
            yy, mm, dd = yyMMdd[:2], yyMMdd[2:4], yyMMdd[4:6]
            year = int(yy)
            year += 2000 if year < 30 else 1900
            return f"{dd}/{mm}/{year}"
        except:
            return ""

    # Try normal date pattern
    all_dates = re.findall(r"\d{2}/\d{2}/\d{4}", text)
    date_of_issue = all_dates[0] if len(all_dates) > 0 else ""
    date_of_expiry = all_dates[1] if len(all_dates) > 1 else ""

    # Try MRZ line parsing
    mrz_line = find(r"(P[0-9A-Z<]{40,})")
    if mrz_line:
        print("MRZ line:", mrz_line)
        passport_match = re.match(r"([A-Z][0-9]{7})", mrz_line)
        expiry_match = re.search(r"M(\d{6})", mrz_line)

        if passport_match:
            passport_number = passport_match.group(1)
        else:
            passport_number = find(r"\b([A-Z][0-9]{7})\b", "")

        if expiry_match:
            mrz_expiry = expiry_match.group(1)
            date_of_expiry = format_date(mrz_expiry)
            if not date_of_issue:
                try:
                    year = int(date_of_expiry[-4:])
                    date_of_issue = date_of_expiry.replace(str(year), str(year - 10))
                except:
                    pass
    else:
        passport_number = find(r"\b([A-Z][0-9]{7})\b", "")

    data = {
        "passport_number": passport_number,
        "surname": find(r"Surname\s*\n(.+)", ""),
        "given_names": find(r"Given Name[s]?\s*\n(.+)", ""),
        "nationality": find(r"Nationality\s*/\s*(.+)", find(r"Nationality\s*\n(.+)", "")),
        "sex": find(r"Sex\s*/\s*(M|F)", find(r"\b(M|F)\b", "")),
        "date_of_birth": find(r"Date of Birth\s*\n(\d{2}/\d{2}/\d{4})", ""),
        "place_of_birth": find(r"Place of Birth\s*\n(.+)", ""),
        "place_of_issue": find(r"Place of Issue\s*\n(.+)", ""),
        "date_of_issue": date_of_issue,
        "date_of_expiry": date_of_expiry,
        "father_name": find(r"Name of Father[^\n]*\n(.+)", ""),
        "mother_name": find(r"Name of Mother[^\n]*\n(.+)", ""),
        "spouse_name": find(r"Name of Spouse[^\n]*\n(.+)", ""),
        "address": find(r"Address\s*\n(.+(?:\n.+)+)", "")
    }

    return data

def extract_passport_data(text):
    """
    Extract passport details, including full name (first, middle, last).
    Falls back gracefully if “Given Names” or “Surname” aren’t found.
    """

    def find(pattern):
        m = re.search(pattern, text, re.IGNORECASE)
        return m.group(1).strip() if m and m.group(1) else ""

    all_dates = re.findall(r"\d{2}/\d{2}/\d{4}", text)
    date_of_issue = all_dates[0] if len(all_dates) > 0 else ""
    date_of_expiry = all_dates[1] if len(all_dates) > 1 else ""

    lines = text.splitlines()
    given_names = ""
    surname = ""

    for i, line in enumerate(lines):
        if re.search(r"Given Name[s]?", line, re.IGNORECASE):
            parts = line.split(":")
            if len(parts) > 1 and parts[1].strip() and parts[1].strip().lower() != "(s)":
                given_names = parts[1].strip()
            elif i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and next_line.lower() != "(s)":
                    given_names = next_line
        elif re.search(r"Surname", line, re.IGNORECASE):
            parts = line.split(":")
            if len(parts) > 1 and parts[1].strip():
                surname = parts[1].strip()
            elif i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line:
                    surname = next_line

    if not given_names and not surname:
        mrz = find(r"(P[0-9A-Z<]{40,})")
        if mrz:
            parts = mrz[2:].split("<<", 1)
            if len(parts) == 2:
                raw_surname, raw_given = parts[0], parts[1]
                surname = raw_surname.replace("<", " ").strip().title()
                given_names = raw_given.replace("<", " ").strip().title()

    full_name = (given_names + " " + surname).strip()

    first_name = middle_name = last_name = ""
    if full_name:
        parts = full_name.split()
        if len(parts) == 1:
            first_name = parts[0]
        elif len(parts) == 2:
            first_name, last_name = parts
        else:
            first_name = parts[0]
            last_name = parts[-1]
            middle_name = " ".join(parts[1:-1])

    # Extract father_name and other fields before fallback logic
    father_name = find(r"Name of Father[^\n]*\n(.+)")
    mother_name = find(r"Name of Mother[^\n]*\n(.+)")
    spouse_name = find(r"Name of Spouse[^\n]*\n(.+)")
    nationality = find(r"Nationality\s*[\/]?\s*(.+)")
    sex = find(r"Sex\s*[\/]?\s*(M|F)")
    date_of_birth = find(r"Date of Birth\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})")
    place_of_birth = find(r"Place of Birth\s*[:\-]?\s*(.+)")
    place_of_issue = find(r"Place of Issue\s*[:\-]?\s*(.+)")
    address = find(r"Address\s*\n(.+(?:\n.+)+)")

    # Fallback: if middle_name empty, use first word of father's name if present
    if not middle_name and father_name:
        father_parts = father_name.strip().split()
        if father_parts:
            middle_name = father_parts[0]

    passport_number = ""
    mrz_line = find(r"(P[0-9A-Z<]{40,})")
    if mrz_line:
        m = re.match(r"([A-Z][0-9]{7})", mrz_line)
        passport_number = m.group(1) if m else find(r"\b([A-Z][0-9]{7})\b")
    else:
        passport_number = find(r"\b([A-Z][0-9]{7})\b")

    if mrz_line:
        exp_match = re.search(r"M(\d{6})", mrz_line)
        if exp_match:
            yyMMdd = exp_match.group(1)
            try:
                yy, mm, dd = yyMMdd[:2], yyMMdd[2:4], yyMMdd[4:6]
                y = int(yy) + (2000 if int(yy) < 30 else 1900)
                date_of_expiry = f"{dd}/{mm}/{y}"
                if not date_of_issue:
                    i_year = y - 10
                    date_of_issue = f"{dd}/{mm}/{i_year}"
            except:
                pass

    data = {
        "full_name": full_name or None,
        "first_name": first_name or None,
        "middle_name": middle_name or None,
        "last_name": last_name or None,
        "passport_number": passport_number or None,
        "date_of_issue": date_of_issue or None,
        "date_of_expiry": date_of_expiry or None,
        "nationality": nationality or None,
        "sex": sex or None,
        "date_of_birth": date_of_birth or None,
        "place_of_birth": place_of_birth or None,
        "place_of_issue": place_of_issue or None,
        "father_name": father_name or None,
        "mother_name": mother_name or None,
        "spouse_name": spouse_name or None,
        "address": address or None
    }
    return data


def extract(pattern, text, default=""):
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else default


def extract_cv_features(text):
    lower_text = text.lower()
    word_count = len(text.split())

    sections = {
        "about_me": "about me" in lower_text,
        "education": "education" in lower_text,
        "experience": "experience" in lower_text,
        "skills": "skills" in lower_text,
        "references": "references" in lower_text
    }

    email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    phone_match = re.search(r"\+91\s?\d{5}\s?\d{4}", text)
    date_range_match = re.search(r"\b(19|20)\d{2}\s*[-–]\s*(19|20)\d{2}\b", text)

    coding_keywords = ["python", "java", "c++", "c#", "javascript", "html", "css", "react", "node", "sql", "typescript"]
    coding_found = [lang for lang in coding_keywords if lang in lower_text]

    return {
        "sections_found": sections,
        "email": email_match.group() if email_match else None,
        "phone": phone_match.group(0).strip() if phone_match else "",
        "date_range": date_range_match.group() if date_range_match else None,
        "coding_languages": coding_found,
        "word_count": word_count
    }