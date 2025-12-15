# Security Notice: Private Key Rotation Required

## ⚠️ IMPORTANT - Action Required

The RSA private key file `kalshi/kc.txt` was **previously committed to git** and has now been removed from the repository history. However, **anyone who had access to the repository before this cleanup may still have a copy of the key.**

## Immediate Actions Required:

### 1. **Rotate Your API Keys** (CRITICAL)
- Log in to your Kalshi account (demo.kalshi.co or kalshi.com)
- Go to **Settings → API Keys**
- **Delete the compromised API key**
- Generate a new API key and download the new private key file
- Update your `.env` file with the new credentials

### 2. **Verify Repository Access**
- Review who has had access to this repository
- Consider making the repository private if it was public
- Rotate credentials for anyone who may have cloned the repository

### 3. **Update Your Configuration**

You now have two options for configuring your private key:

#### Option A: Inline Private Key (Recommended for Cloud/Railway)
```bash
# In your .env file:
KALSHI_API_KEY_ID=your_new_api_key_id
KALSHI_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
...your key content here...
-----END RSA PRIVATE KEY-----"
```

**Note:** For multi-line keys in .env, you can either:
- Use literal newlines (most .env parsers support this)
- Or replace newlines with `\n` (code will handle this)

#### Option B: File Path (For Local Development Only)
```bash
# Store your new key file outside the git repository
KALSHI_API_KEY_ID=your_new_api_key_id
KALSHI_PRIVATE_KEY_PATH=/secure/path/outside/repo/new_private_key.pem
```

## What Was Done:

✅ Added `kalshi/`, `kc.txt`, and `*.pem` to `.gitignore`  
✅ Removed `kalshi/kc.txt` from git index  
✅ Cleaned entire git history using `git filter-branch`  
✅ Force-pushed to remote to update repository  
✅ Updated code to support inline private keys  

## Best Practices Going Forward:

1. **Never commit private keys or secrets to git**
2. **Always use `.gitignore` for sensitive files**
3. **For cloud deployments:** Use environment variables or secret managers
4. **For local development:** Store keys outside the repository directory
5. **Regularly rotate API keys** as a security best practice
6. **Use separate keys** for demo and production environments

## Verification:

To verify the key is removed from history:
```bash
git log --all --full-history -- kalshi/kc.txt
# Should return no results
```

## Need Help?

- Kalshi API Security: Contact Kalshi support
- Repository Questions: Check the MIGRATION.md and README.md

---

**Date Cleaned:** December 15, 2025  
**Method Used:** git filter-branch with full history rewrite
