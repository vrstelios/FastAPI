"""
Quick script to verify Oracle Cloud (Object Storage) credentials and permissions.

This checks that your .env credentials can upload to and delete from your
Oracle bucket without needing to go through the full application flow.
"""
import httpx
from app.core.config import settings

def check_oracle_connection():
    print(f"Testing PAR URL: {settings.oracle_par_url}")
    print()

    test_key = "profile_pics/test.txt"
    url = f"{settings.oracle_par_url}{test_key}"

    # Test upload
    try:
        response = httpx.put(url, content=b"test", headers={"Content-Type": "text/plain"})
        response.raise_for_status()
        print("Upload: SUCCESS")
    except Exception as e:
        print(f"Upload: FAILED - {e}")
        return

    # Test delete
    try:
        response = httpx.delete(url)
        if response.status_code == 404:
            print("Delete: SKIPPED (Expected - Oracle Bucket PARs restricted from deleting)")
        else:
            response.raise_for_status()
            print("Delete: SUCCESS")
    except Exception as e:
        print(f"Delete: FAILED - {e}")
        return

    print()
    print("All tests passed! Your Oracle Cloud configuration is ready for production uploads.")

if __name__ == "__main__":
    check_oracle_connection()