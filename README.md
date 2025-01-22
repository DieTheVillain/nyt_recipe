# NYT Recipe Scraper

A Python-based utility to scrape recipes from the [New York Times Cooking](https://cooking.nytimes.com/) website and export them as HTML or PDF files. This tool extracts the recipe title, ingredients, instructions, and optionally includes images. It is based on the work of Ian Brault found at https://github.com/ianbrault/nyt_recipe

---

## Features
- Extract recipes from NYT Cooking.
- Export recipes in HTML or PDF format.

---

## Installation

### Prerequisites
1. **Python 3.7 or higher**: Download and install Python from [python.org](https://www.python.org/downloads/).
2. **`wkhtmltopdf`**: This is required for PDF generation.
    - Download from [wkhtmltopdf.org](https://wkhtmltopdf.org/downloads.html).
    - Install the appropriate version for your operating system.
    - Ensure `wkhtmltopdf` is added to your system's PATH:
        - **Windows**: Add the installation directory (e.g., `C:\Program Files\wkhtmltopdf\bin`) to your PATH environment variable.
        - **Linux/Mac**: Add the binary's location (e.g., `/usr/local/bin`) to your PATH.

### Installing Python Dependencies
1. Clone the repository or download the ZIP:
   ```bash
   git clone https://github.com/yourusername/nyt-recipe-scraper.git
   cd nyt-recipe-scraper
2.
   ```bash
   pip install -r requirements.txt

The key dependencies include:
  - beautifulsoup4 for parsing HTML.
  - wkhtmltopdf for PDF rendering.

---

## Usage

### Basic Syntax
Run the script using the following command:

  ```bash
  python main.py [options] <NYT_recipe_URL>
  ```

### Options
  - -d, --debug: Enables debug output for troubleshooting.
  - -o, --output-dir <directory>: Specifies the directory to save the exported file(s).
  - -f, --format <html|pdf>: Specifies the export format (html or pdf).
  - -h, --help: Displays usage information.
-h, --help: Displays usage information.
-h, --help: Displays usage information.
-h, --help: Displays usage information.

## Examples

### Export a Recipe to PDF
  ```bash
  python main.py -o C:\recipes\ -f pdf https://cooking.nytimes.com/recipes/1013451-longevity-noodles-with-chicken-ginger-and-mushrooms
  ```

### Export a Recipe to HTML with Debugging
  ```bash
  python main.py -d -o ./recipes/ -f html https://cooking.nytimes.com/recipes/1013451-longevity-noodles-with-chicken-ginger-and-mushrooms

  ```

---

## Adding wkhtmltopdf to PATH

### Windows
1. Locate the wkhtmltopdf installation directory (e.g., C:\Program Files\wkhtmltopdf\bin).
2. Open the Start Menu and search for "Environment Variables."
3. In the System Properties window, click Environment Variables.
4. Under "System Variables," find the Path variable, select it, and click Edit.
5. Add the full path to the bin directory of wkhtmltopdf and click OK to save.

### Linux/Mac
1. Add the path of wkhtmltopdf to your shell configuration file:
  ```bash
  export PATH="/path/to/wkhtmltopdf:$PATH"
  ```
2. Reload your shell configuration:
  ```bash
  source ~/.bashrc  # or ~/.zshrc, depending on your shell
  ```

---

## Known Issues
1. Fractional Measurements: Special characters like ¼, ½, ¾ are properly sanitized and displayed as HTML entities for correct rendering.
2. Debugging Errors: Use the -d flag to enable debug output for troubleshooting.

---

## Contributing
Feel free to submit pull requests or raise issues for any bugs or feature requests.

---

## License
This project is licensed under the MIT License. See LICENSE.txt for details.

---


### Key Features:
1. **Installation**: Provides detailed steps for installing dependencies (`beautifulsoup4`, `wkhtmltopdf`) and configuring `PATH`.
2. **Usage Examples**: Includes practical examples for exporting recipes in different formats.
3. **Debugging and Known Issues**: Mentions common errors and solutions. 

Let me know if any specific adjustments are needed!
