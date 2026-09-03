#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "build-src")
path = root / "app/src/test/kotlin/com/example/directive/data/portability/BackupCodecTest.kt"
text = path.read_text(encoding="utf-8")

old = '''    @Test fun validContentUriAttachmentAccepted() {
        val a = AttachmentEntity("a","t","x",null,AttachmentStorageMode.SAF_URI,"content://provider/id",createdAt=1L)
        assertTrue(BackupCodec.validate(clean().copy(attachments=listOf(a))).valid)
    }
'''
new = '''    @Test fun validContentUriAttachmentAccepted() {
        val a = AttachmentEntity("a","t","x",null,AttachmentStorageMode.SAF_URI,"content://provider/id",createdAt=1L)
        val payload = BackupAttachmentPayload("a", "eA==")
        assertTrue(BackupCodec.validate(clean().copy(attachments=listOf(a), attachmentPayloads=listOf(payload))).valid)
    }

    @Test fun schemaV2AttachmentWithoutPortableContentRejected() {
        val a = AttachmentEntity("a","t","x",null,AttachmentStorageMode.SAF_URI,"content://provider/id",createdAt=1L)
        assertFalse(BackupCodec.validate(clean().copy(attachments=listOf(a))).valid)
    }
'''

if new in text:
    print("BACKUP_TEST_CONVERGENCE=PASS changed=0")
elif old in text:
    text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")
    print("BACKUP_TEST_CONVERGENCE=PASS changed=1")
else:
    raise SystemExit("Expected BackupCodecTest SAF URI test block not found exactly once")
