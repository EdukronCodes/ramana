#!/usr/bin/env python3
"""
Main entry point for the PDF Processor MCP Server
"""

import asyncio
import sys
from src import main

if __name__ == "__main__":
    asyncio.run(main())
