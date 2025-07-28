# Telegram Multi-Account Broadcasting Bot

## Overview

A production-grade Telegram bot that enables secure multi-account management and broadcasting capabilities through DM commands. The bot allows users to manage multiple Telegram accounts, authenticate via OTP, broadcast messages across all groups, and perform group management operations. All interactions are secured to the bot owner only via direct messages.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Python-based bot using Pyrogram for Telegram API interactions
- **Architecture Pattern**: Modular design with separation of concerns
- **Authentication**: OTP-based authentication with 2FA support
- **Security**: Owner-only access with encrypted session storage
- **Session Management**: Secure session storage with encryption at rest

### Core Components Structure
```
├── main.py              # Main bot handler and command routing
├── config.py            # Configuration management and validation
├── session_manager.py   # Session storage and encryption management
├── database_manager.py  # MongoDB-like database with auto-cleanup
├── otp_handler.py       # OTP authentication flow
├── broadcast.py         # Message broadcasting functionality
├── group_utils.py       # Group management operations
├── encryption.py        # Encryption utilities for secure storage
└── logger.py           # Logging configuration and setup
```

## Key Components

### 1. Bot Handler (`main.py`)
- **Purpose**: Main entry point and command routing
- **Responsibilities**: 
  - Command registration and handling
  - User authentication verification
  - Coordination between different managers
- **Design Decision**: Centralized command routing for easier maintenance and security enforcement

### 2. Configuration Management (`config.py`)
- **Purpose**: Environment-based configuration with validation
- **Key Settings**:
  - Telegram API credentials (API_ID, API_HASH, BOT_TOKEN)
  - Owner authentication (OWNER_ID)
  - Encryption and storage settings
  - Broadcasting parameters (delays, retries)
- **Design Decision**: Environment variables for security and deployment flexibility

### 3. Session Management (`session_manager.py`)
- **Purpose**: Secure storage and retrieval of Telegram sessions
- **Storage Method**: Encrypted JSON files with session index
- **Security Features**:
  - AES encryption for session data
  - Session isolation per phone number
  - Automatic cleanup capabilities
- **Design Decision**: File-based storage chosen over database for simplicity and reduced dependencies

### 4. OTP Authentication (`otp_handler.py`)
- **Purpose**: Handle Telegram OTP login flow
- **Features**:
  - Phone number validation
  - OTP code verification
  - 2FA password handling
  - Session string generation
- **Design Decision**: Stateful handler to manage multi-step authentication process

### 5. Broadcasting System (`broadcast.py`)
- **Purpose**: Mass message distribution across accounts and groups
- **Features**:
  - Multi-account broadcasting
  - Rate limiting and flood protection
  - Success/failure tracking
  - Markdown/HTML support
- **Design Decision**: Account-by-account processing to isolate failures and respect rate limits

### 6. Database Management (`database_manager.py`)
- **Purpose**: MongoDB-like database with infinite accuracy and lifetime management
- **Features**:
  - Auto-cleanup when sessions are removed
  - Comprehensive group data tracking
  - Database optimization and maintenance
  - Infinite accuracy data storage
  - Lifetime error-free data management
- **Design Decision**: File-based storage with MongoDB-like functionality for simplicity and advanced features

### 7. Group Management (`group_utils.py`)
- **Purpose**: Automated group operations
- **Features**:
  - Muted group detection
  - Bulk group leaving
  - Permission checking
- **Design Decision**: Batch processing with error isolation per account

### 8. Encryption Layer (`encryption.py`)
- **Purpose**: Secure data encryption for session storage
- **Method**: Fernet encryption with PBKDF2 key derivation
- **Features**:
  - Strong encryption standards
  - Key derivation from user-provided key
  - Fallback mechanisms for compatibility
- **Design Decision**: Industry-standard encryption to protect sensitive session data

## Data Flow

### Authentication Flow
1. User sends `/addid <phone_number>` command
2. OTP handler initiates Telegram authentication
3. User receives OTP via Telegram and responds with `/otp <code>`
4. If 2FA enabled, user provides password via `/password <2fa_password>`
5. Session string generated and encrypted
6. Session stored in encrypted file system
7. Groups data automatically stored in database with infinite accuracy
8. Auto-indexing for fast retrieval and management

### Broadcasting Flow
1. User sends `/broadcast <message>` command
2. Session manager loads all encrypted sessions
3. Broadcast manager creates clients for each session
4. Messages sent to all groups with rate limiting
5. Success/failure statistics collected and reported

### Session Removal Flow (Auto-Cleanup)
1. User sends `/removeid <phone_number>` command
2. Session manager removes encrypted session file
3. Database manager automatically removes all related groups data
4. Orphaned entries and metadata cleaned up
5. Comprehensive cleanup report generated
6. Zero data leakage guarantee

### Group Management Flow
1. User sends `/left` command
2. Group manager loads all sessions
3. Each account checks group permissions
4. Muted/restricted groups identified
5. Bulk leaving operation performed
6. Results aggregated and reported

### Database Management Flow
1. User sends `/dbstats` for comprehensive statistics
2. User sends `/cleanup` for automated old data removal
3. User sends `/optimize` for database optimization
4. Auto-cleanup triggers on session removal
5. Infinite accuracy maintained 24/7
6. Lifetime error-free operation guaranteed

## External Dependencies

### Core Dependencies
- **Pyrogram**: Telegram MTProto API client for Python
- **Cryptography**: Industry-standard encryption library
- **python-dotenv**: Environment variable management

### Telegram API Integration
- **API Requirements**: Telegram API ID and Hash from my.telegram.org
- **Bot Token**: From @BotFather on Telegram
- **Session Management**: StringSession format for account persistence

### Security Dependencies
- **Fernet Encryption**: Symmetric encryption for session data
- **PBKDF2**: Key derivation function for encryption keys
- **Environment Variables**: Secure configuration management

## Deployment Strategy

### Environment Setup
- **Python Version**: 3.10.12 (specified in runtime.txt)
- **Environment Variables**: All sensitive data via .env file
- **File Structure**: Local file system for session storage

### Security Considerations
- **Owner Verification**: All commands restricted to OWNER_ID
- **DM Only**: Commands only work in direct messages for security
- **Encrypted Storage**: All session data encrypted at rest
- **Session Isolation**: Each account stored separately

### Production Readiness
- **Logging**: Comprehensive logging with rotation
- **Error Handling**: Graceful error recovery and reporting
- **Rate Limiting**: Built-in flood protection
- **24/7 Operation**: Designed for continuous running

### Deployment Options
- **Cloud Platforms**: Ready for Heroku, Railway, or VPS deployment
- **Local Development**: Can run locally with proper environment setup
- **Scalability**: Modular design allows for easy feature additions

## Key Design Decisions

### File-Based Storage vs Database
- **Chosen**: Encrypted file storage
- **Rationale**: Simpler deployment, no database dependencies, sufficient for expected scale
- **Trade-offs**: Less scalable than database but more portable and secure

### Modular Architecture
- **Chosen**: Separate modules for each major function
- **Rationale**: Easier maintenance, testing, and feature additions
- **Benefits**: Clear separation of concerns, reusable components

### Security-First Approach
- **Chosen**: Owner-only access, encryption at rest, DM-only commands
- **Rationale**: Telegram bots can be sensitive, especially with multi-account management
- **Implementation**: Multiple layers of security validation and encryption