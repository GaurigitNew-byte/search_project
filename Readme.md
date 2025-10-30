# Clone the repository
git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>

# Create a virtual environment
python version 3.13.7
python -m venv venv

# Activate the virtual environment
venv\Scripts\activate   

# Install dependencies
pip install -r requirements.txt

# Create a .env file in the project root directory
LOGIN=your_dataforseo_username
PASSWORD=your_dataforseo_password

# Run migrations
python manage.py migrate

# Start the server
python manage.py runserver

# Open this URL in your browser
http://127.0.0.1:8000/

# Enter search queries -> Click "Search" -> Download as CSV if needed
