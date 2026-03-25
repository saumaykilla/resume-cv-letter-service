# Resume CV Letter Service 📝✨

**AI-Powered Document Generation Microservice**

A production-grade microservice for automatically generating tailored resumes, CVs, and cover letters using AI with containerized deployment on AWS Lambda.

---

## 🌟 Features

- 📄 **Resume Generation** - AI-powered resume creation
- 🎓 **CV Creation** - Comprehensive curriculum vitae
- ✍️ **Cover Letter** - Personalized cover letters
- 🎯 **Customization** - Tailor to job descriptions
- 🤖 **AI Enhancement** - Content improvement
- 💾 **PDF Export** - Download generated documents
- 🔄 **Batch Processing** - Generate multiple documents
- 🐳 **Containerized** - Docker support

---

## 🛠️ Tech Stack

**Core:**
- Python 3.10+
- FastAPI (optional API wrapper)
- reportlab (PDF generation)
- python-docx (DOCX generation)

**AI/LLM:**
- OpenAI API / Anthropic
- LangChain (optional)

**Infrastructure:**
- Docker
- AWS Lambda

---

## 📊 Language Composition

```
Python: 98.5%
Dockerfile: 1.5%
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- OpenAI API key (or alternative LLM)
- Docker (optional)

### Installation

```bash
# Clone the repository
git clone https://github.com/saumaykilla/resume-cv-letter-service.git
cd resume-cv-letter-service

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Setup

Create `.env`:

```env
OPENAI_API_KEY=your_api_key
LLM_MODEL=gpt-3.5-turbo
OUTPUT_FORMAT=pdf  # or docx
```

---

## 📁 Project Structure

```
resume-cv-letter-service/
├── src/
│   ├── __init__.py
│   ├── resume_generator.py    # Resume generation
│   ├── cv_generator.py        # CV generation
│   ├── letter_generator.py    # Cover letter
│   ├── pdf_builder.py         # PDF formatting
│   ├── docx_builder.py        # DOCX formatting
│   ├── llm_handler.py         # LLM integration
│   ├── models.py              # Data models
│   ├── config.py              # Configuration
│   └── utils.py               # Utilities
├── templates/
│   ├── resume_template.html   # Resume HTML template
│   ├── cv_template.html       # CV HTML template
│   └── letter_template.html   # Letter HTML template
├── tests/
│   ├── test_generators.py
│   ├── test_builders.py
│   └── test_llm.py
├── examples/
│   ├── sample_user_data.json
│   └── example_usage.py
├── Dockerfile
├── requirements.txt
├── lambda_handler.py
└── README.md
```

---

## 🔧 Core Components

### Resume Generator

```python
from src.resume_generator import ResumeGenerator

generator = ResumeGenerator()

# Generate resume
resume = generator.generate(
    user_data={
        'name': 'John Doe',
        'email': 'john@example.com',
        'phone': '+1234567890',
        'summary': 'Experienced developer...',
        'experience': [...],
        'education': [...],
        'skills': [...]
    },
    job_description='Senior Python Developer...'
)

# Export to PDF
resume.to_pdf('resume.pdf')
```

### CV Generator

```python
from src.cv_generator import CVGenerator

generator = CVGenerator()

# Generate CV
cv = generator.generate(
    user_data=user_data,
    include_certifications=True,
    include_publications=True
)

# Export to DOCX
cv.to_docx('cv.docx')
```

### Cover Letter Generator

```python
from src.letter_generator import CoverLetterGenerator

generator = CoverLetterGenerator()

# Generate letter
letter = generator.generate(
    user_name='John Doe',
    company_name='Acme Corp',
    position='Senior Developer',
    company_description='...',
    custom_notes='...'
)

# Export to PDF
letter.to_pdf('cover_letter.pdf')
```

---

## 💻 Usage Examples

### Basic Generation

```python
from src.resume_generator import ResumeGenerator

# User data
user_data = {
    'name': 'Jane Smith',
    'email': 'jane@example.com',
    'phone': '+1234567890',
    'location': 'New York, NY',
    'summary': 'Full-stack developer with 5 years experience',
    'experience': [
        {
            'company': 'Tech Corp',
            'position': 'Senior Developer',
            'duration': '2020-2023',
            'responsibilities': ['Led team', 'Developed APIs']
        }
    ],
    'education': [
        {
            'school': 'State University',
            'degree': 'BS Computer Science',
            'year': 2018
        }
    ],
    'skills': ['Python', 'JavaScript', 'AWS', 'Docker']
}

# Generate
generator = ResumeGenerator()
resume = generator.generate(user_data)

# Export
resume.to_pdf('resume.pdf')
```

### AI Customization

```python
from src.resume_generator import ResumeGenerator

generator = ResumeGenerator(use_ai=True)

# Job description to tailor to
job_desc = """
Senior Python Developer
- 5+ years Python experience
- AWS expertise
- Team leadership
"""

# Generate tailored resume
resume = generator.generate(
    user_data=user_data,
    job_description=job_desc,
    tailoring_mode='aggressive'  # or 'moderate', 'conservative'
)

resume.to_pdf('tailored_resume.pdf')
```

### Batch Generation

```python
from src.resume_generator import ResumeGenerator
from src.cv_generator import CVGenerator
from src.letter_generator import CoverLetterGenerator

resume_gen = ResumeGenerator()
cv_gen = CVGenerator()
letter_gen = CoverLetterGenerator()

# Generate all documents
documents = {
    'resume': resume_gen.generate(user_data),
    'cv': cv_gen.generate(user_data),
    'cover_letter': letter_gen.generate(
        user_name=user_data['name'],
        company_name='Target Company',
        position='Target Position'
    )
}

# Export all
for doc_type, doc in documents.items():
    doc.to_pdf(f'{doc_type}.pdf')
```

### With JSON Input

```python
import json
from src.resume_generator import ResumeGenerator

# Load from JSON
with open('profile.json', 'r') as f:
    user_data = json.load(f)

# Generate
generator = ResumeGenerator()
resume = generator.generate(user_data)

# Export
resume.to_pdf('resume.pdf')
```

---

## 📋 Data Models

### User Data Schema

```python
{
    'name': str,
    'email': str,
    'phone': str,
    'location': str,
    'summary': str,
    'experience': [
        {
            'company': str,
            'position': str,
            'duration': str,
            'location': str,
            'responsibilities': [str],
            'achievements': [str]
        }
    ],
    'education': [
        {
            'school': str,
            'degree': str,
            'field': str,
            'year': int,
            'gpa': float (optional)
        }
    ],
    'skills': [str],
    'certifications': [
        {
            'name': str,
            'issuer': str,
            'date': str
        }
    ],
    'projects': [
        {
            'name': str,
            'description': str,
            'technologies': [str]
        }
    ]
}
```

---

## 🎨 Output Formats

### PDF Export

```python
resume.to_pdf('resume.pdf', format='A4')
```

### DOCX Export

```python
resume.to_docx('resume.docx')
```

### HTML Export

```python
html = resume.to_html()
```

---

## 🚀 Deployment

### AWS Lambda

```bash
# Package
zip -r function.zip src/ lambda_handler.py requirements.txt

# Deploy
aws lambda create-function \
  --function-name resume-service \
  --runtime python3.10 \
  --handler lambda_handler.handler \
  --zip-file fileb://function.zip
```

### Docker

```bash
# Build
docker build -t resume-service .

# Run
docker run -e OPENAI_API_KEY=key resume-service
```

---

## ⚙️ Configuration

### Generator Settings

```python
# config.py
MAX_RESUME_LENGTH = 1  # pages
MAX_CV_LENGTH = 3      # pages
PDF_FONT = 'Arial'
PDF_SIZE = 11          # points
AI_MODEL = 'gpt-3.5-turbo'
TEMPERATURE = 0.7
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_generators.py

# With coverage
pytest --cov=src
```

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/Enhancement`)
3. Commit changes (`git commit -m 'Add Enhancement'`)
4. Push to branch (`git push origin feature/Enhancement`)
5. Open Pull Request

---

## 📝 License

MIT License - see LICENSE file for details

---

## 📞 Support

For issues or questions:
- Open a GitHub issue
- Email: [saumay.killa@gmail.com](mailto:saumay.killa@gmail.com)

---

## 🔗 Links

- **GitHub**: [https://github.com/saumaykilla/resume-cv-letter-service](https://github.com/saumaykilla/resume-cv-letter-service)

---

<div align="center">

**Professional Documents Generated by AI**

Made with ❤️ by Saumay Killa

[⬆ back to top](#resume-cv-letter-service-)

</div>
