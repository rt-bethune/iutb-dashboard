#!/usr/bin/env python3
"""
Seed the database with demo data (users, budgets, recruitment).
Run this script when you need sample data for development/testing.

Usage:
    python scripts/seed_data.py [--force]

Options:
    --force    Delete existing data before seeding
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

if __name__ == "__main__":
    from app.seeds import main
    main()
