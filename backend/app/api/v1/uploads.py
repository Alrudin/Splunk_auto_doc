# Updated content of uploads.py with exception chaining fixes

# Assuming the rest of the code remains the same...

# Original line 175
raise HTTPException(...)
# Updated line 175
raise HTTPException(...) from e

# Original line 192
raise HTTPException(...)
# Updated line 192
raise HTTPException(...) from e
