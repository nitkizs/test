## Download Data from LakeFS

This section describes how to download images from lakeFS using S3-compatible tools.
LakeFS provides an **S3 compatible API**, which allows data access using standard tools such as the AWS CLI.

---

### Step 1: Install AWS CLI

Download and install AWS CLI from the official documentation:
[https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)

For Windows (PowerShell):

```powershell
msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi
```

Verify installation:

```powershell
aws --version
```

---

### Step 2: Configure AWS CLI for lakeFS

Run the following command:

```powershell
aws configure
```

Provide your **lakeFS credentials** (not AWS credentials):

```
AWS Access Key ID:     <lakefs_access_key>
AWS Secret Access Key: <lakefs_secret_key>
Default region name:   us-east-1
Default output format: json
```

> Note: Region and output format values can be set to any valid value.

---

### Step 3: Download Images

Use the following command to download images:

```powershell
aws s3 cp "s3://<repository>/<branch>/<path>" "<local_destination>" --recursive --endpoint-url "http://ai-lakefs:8000"
```

**Example:**

```powershell
aws s3 cp "s3://uaiv-dataset/main/images-mu" "D:\Draive\Data Sets\mavic" --recursive --endpoint-url "http://ai-lakefs:8000"
```

---

### Notes

* Replace the following values based on your setup:

  * `<repository>` → lakeFS repository name
  * `<branch>` → branch name (e.g., `main`)
  * `<path>` → directory inside the repository

* Ensure you have access permissions to the repository

* The destination folder will be created automatically if it does not exist

---

