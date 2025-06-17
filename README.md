# Contentful Migration Tools

A comprehensive migration system to transfer content from Contentful to various destinations including Squidex schemas, AWS S3 assets, and MongoDB content.

## 🚀 Features

- **Schema Migration**: Migrate Contentful content types to Squidex
- **Asset Migration**: Transfer Contentful assets to AWS S3 with organized folder structure
- **Content Migration**: Migrate Contentful entries to MongoDB with reference resolution
- **Automatic Dependency Installation**: Scripts auto-install required packages
- **Clean Deletion**: Remove migrated data from destinations

## 📋 Prerequisites

- Python 3.7+
- Virtual environment (recommended)
- Contentful account with API access
- AWS account with S3 access (for asset migration)
- MongoDB Atlas account (for content migration)
- Squidex instance (for schema migration)

## 🛠 Installation & Setup

### 1. Clone and Setup Environment

```bash
# Navigate to project directory
cd squidix-local

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows
```

### 2. Install Dependencies

```bash
# Activate virtual environment first
source venv/bin/activate

# Install all dependencies from requirements.txt
pip install -r requirements.txt

# Or install individually:
pip install boto3>=1.34.0
pip install requests>=2.31.0
pip install python-dotenv>=1.0.0
pip install click>=8.1.0
pip install pillow>=10.0.0
pip install pymongo>=4.6.0
```

### 3. Environment Configuration

Update the `.env` file with your credentials:

```bash
# AWS Credentials for S3 Asset Store
SQUIDEX_AWS_ACCESS_KEY_ID=your_aws_access_key
SQUIDEX_AWS_SECRET_ACCESS_KEY=your_aws_secret_key
SQUIDEX_S3_BUCKET_NAME=your_s3_bucket_name
SQUIDEX_S3_REGION=ap-southeast-2

# Contentful Details
CONTENTFUL_SPACE_ID="your_contentful_space_id"
CONTENTFUL_ENVIRONMENT_ID="your_environment_id"
CONTENTFUL_CMA_TOKEN="your_contentful_token"

# Squidex Details (for schema migration)
SQUIDEX_URL="http://localhost:8080"
SQUIDEX_APP_NAME="your_app_name"
SQUIDEX_CLIENT_ID="your_client_id"
SQUIDEX_CLIENT_SECRET="your_client_secret"

# MongoDB Configuration (for content migration)
MONGODB_CONNECTION_STRING="mongodb+srv://username:password@cluster.mongodb.net/database?retryWrites=true&w=majority"
MONGODB_DATABASE_NAME="your_database_name"
```

## 🎯 Usage

### Schema Migration (Contentful → Squidex)

```bash
# Migrate content types/schemas to Squidex
source venv/bin/activate && python contentful_squidx_schemas_migration.py

# Delete migrated schemas from Squidex
source venv/bin/activate && python delete_migrated_schemas.py
```

### Asset Migration (Contentful → AWS S3)

```bash
# Migrate assets to S3 (limit: 100 assets)
source venv/bin/activate && python contentful_s3_assets_migration.py

# Delete assets from S3
source venv/bin/activate && python delete_migrated_assets.py
```

### Content Migration (Contentful → MongoDB)

```bash
# Migrate content entries to MongoDB
source venv/bin/activate && python contentful_mongodb_content_migration.py

# Delete all collections completely from MongoDB (not just documents)
source venv/bin/activate && python delete_migrated_content.py
```

## 📁 Project Structure

```
squidix-local/
├── services/               # Service layer
│   ├── contentful_base.py     # Common Contentful client
│   ├── contentful_schemas.py  # Schema operations
│   ├── contentful_assets.py   # Asset operations
│   ├── contentful_content.py  # Content operations
│   ├── aws_s3.py              # S3 service
│   ├── mongodb.py             # MongoDB service
│   └── squidex.py             # Squidex service
├── core/                   # Core transformation logic
│   ├── transformer.py         # Schema transformation
│   ├── asset_transformer.py   # Asset transformation
│   └── content_transformer.py # Content transformation
├── config/                 # Configuration
│   └── settings.py
├── logs/                   # Log files
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables
└── README.md              # This file
```

## 🔧 Migration Scripts

| Script | Purpose | Limit |
|--------|---------|-------|
| `contentful_squidx_schemas_migration.py` | Migrate schemas to Squidex | All content types |
| `contentful_s3_assets_migration.py` | Migrate assets to S3 | 100 assets |
| `contentful_mongodb_content_migration.py` | Migrate content to MongoDB | 100 entries per type |
| `delete_migrated_schemas.py` | Delete schemas from Squidex | All |
| `delete_migrated_assets.py` | Delete assets from S3 | All |
| `delete_migrated_content.py` | Drop collections from MongoDB | All |

## 🗂 Data Organization

### S3 Asset Structure
```
bucket-name/
└── assets/
    ├── asset-title_filename.jpg
    ├── another-asset_image.png
    └── ...
```

### MongoDB Structure
```
database/
├── content-type-1/          # Collection per content type
│   ├── document1           # Entry with metadata
│   └── document2
├── content-type-2/
└── migration_summary/      # Migration statistics
```

## 🔍 Key Features

### Automatic Dependency Management
- Scripts automatically install missing Python packages
- Manual installation commands provided above

### Error Handling
- Graceful handling of network issues
- Retry logic for failed operations
- Clear error messages

### Security
- URL encoding for special characters in passwords
- Secure credential handling
- Environment variable configuration

### Asset Management
- Uses asset titles for S3 filenames (more readable)
- Handles duplicate filenames with asset IDs
- Links S3 URLs in content references

### Content Management
- Each content type becomes a separate MongoDB collection
- Complete collection deletion (removes content types entirely)
- Asset references linked to S3 URLs

## 🚨 Troubleshooting

### Common Issues

1. **MongoDB Authentication Error**
   - Ensure password special characters are not manually encoded
   - The system auto-handles URL encoding

2. **Contentful API Limits**
   - Scripts respect API rate limits
   - Automatic pagination for large datasets

3. **S3 Upload Failures**
   - Check AWS credentials and permissions
   - Verify S3 bucket exists and is accessible

4. **Network Connectivity**
   - Scripts include retry logic for network issues
   - Check DNS resolution for external services

### Getting Help

1. Check log files in `logs/` directory
2. Verify all environment variables are set correctly
3. Ensure virtual environment is activated
4. Check service-specific documentation

## 📊 Migration Flow

```
Contentful → [Transform] → Destination
    ↓           ↓             ↓
  Content   Normalize     Squidex
  Assets    Transform       S3
 Schemas    Validate    MongoDB
```

## 🔒 Environment Variables Reference

| Variable | Required | Purpose |
|----------|----------|---------|
| `CONTENTFUL_SPACE_ID` | Yes | Contentful space identifier |
| `CONTENTFUL_ENVIRONMENT_ID` | Yes | Contentful environment |
| `CONTENTFUL_CMA_TOKEN` | Yes | Contentful Management API token |
| `SQUIDEX_AWS_ACCESS_KEY_ID` | For S3 | AWS access key |
| `SQUIDEX_AWS_SECRET_ACCESS_KEY` | For S3 | AWS secret key |
| `SQUIDEX_S3_BUCKET_NAME` | For S3 | S3 bucket name |
| `MONGODB_CONNECTION_STRING` | For MongoDB | MongoDB Atlas connection string |
| `MONGODB_DATABASE_NAME` | For MongoDB | Target database name |
| `SQUIDEX_URL` | For Squidex | Squidex instance URL |
| `SQUIDEX_CLIENT_ID` | For Squidex | Squidex app client ID |
| `SQUIDEX_CLIENT_SECRET` | For Squidex | Squidex app secret |

---

**Note**: All migration scripts are designed to run independently. You can migrate schemas, assets, and content separately based on your needs.
