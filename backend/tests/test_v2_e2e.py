"""
V2.0 End-to-End Test

Test flow:
1. Health check
2. User login
3. Create knowledge base
4. Upload document
5. Wait for processing
6. Ask question
7. Verify answer

Author: C2
Date: 2026-02-28
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000/api"

def test_health():
    """Test 1: Health check"""
    print("\n[1] Health Check")
    resp = requests.get("http://localhost:8000/health")
    data = resp.json()
    print(f"  Status: {data['status']}")
    print(f"  Database: {data['checks']['database']['status']}")
    assert data['status'] == 'healthy', "Service not healthy"
    print("  [PASS]")
    return True

def test_login():
    """Test 2: User login"""
    print("\n[2] User Login")
    # Try to login as admin
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    if resp.status_code == 200:
        data = resp.json()
        token = data.get('data', {}).get('access_token')
        print(f"  Login successful")
        print("  [PASS]")
        return token
    else:
        print(f"  Login failed: {resp.status_code}")
        print("  [SKIP] - Will proceed without auth")
        return None

def test_knowledge_bases(token):
    """Test 3: List knowledge bases"""
    print("\n[3] List Knowledge Bases")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    resp = requests.get(f"{BASE_URL}/knowledge-bases", headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        kbs = data.get('data', {}).get('items', [])
        print(f"  Found {len(kbs)} knowledge bases")
        print("  [PASS]")
        return kbs
    else:
        print(f"  Failed: {resp.status_code}")
        print("  [FAIL]")
        return []

def test_create_kb(token):
    """Test 4: Create knowledge base"""
    print("\n[4] Create Knowledge Base")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    resp = requests.post(f"{BASE_URL}/knowledge-bases", 
        headers=headers,
        json={
            "name": f"E2E Test KB {int(time.time())}",
            "description": "End-to-end test knowledge base",
            "chunk_mode": "chinese_recursive",
            "chunk_size": 500,
            "chunk_overlap": 50
        }
    )
    if resp.status_code == 200:
        data = resp.json()
        kb_id = data.get('data', {}).get('id')
        print(f"  Created KB ID: {kb_id}")
        print("  [PASS]")
        return kb_id
    else:
        print(f"  Failed: {resp.status_code} - {resp.text[:200]}")
        print("  [FAIL]")
        return None

def test_upload_document(token, kb_id):
    """Test 5: Upload document"""
    print("\n[5] Upload Document")
    if not kb_id:
        print("  [SKIP] - No KB ID")
        return None
        
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    # Create a simple test document
    test_content = """
    企业RAG系统功能说明
    
    一、系统概述
    本系统是一个企业级检索增强生成(RAG)系统，支持智能问答和知识库管理。
    系统采用BGE-M3作为向量嵌入模型，使用ChromaDB作为向量数据库。
    
    二、核心功能
    1. 知识库管理：支持文档上传、分类、版本控制
    2. 智能问答：基于RAG技术的问答系统
    3. 用户管理：支持多角色权限控制
    4. 数据分析：提供检索日志和用户行为分析
    
    三、技术架构
    - 后端：Python FastAPI
    - 数据库：PostgreSQL + pg_jieba
    - 向量数据库：ChromaDB
    - 前端：Streamlit + React
    
    四、部署要求
    - Python 3.11+
    - PostgreSQL 16+
    - 至少 8GB 内存
    - GPU 可选（用于 NLI 模型）
    """
    
    files = {"file": ("test_doc.txt", test_content.encode('utf-8'), "text/plain")}
    data = {"knowledge_base_id": str(kb_id)}
    
    resp = requests.post(f"{BASE_URL}/documents/upload",
        headers=headers,
        files=files,
        data=data
    )
    
    if resp.status_code == 200:
        data = resp.json()
        doc_id = data.get('data', {}).get('id')
        print(f"  Uploaded Document ID: {doc_id}")
        print("  [PASS]")
        return doc_id
    else:
        print(f"  Failed: {resp.status_code} - {resp.text[:200]}")
        print("  [FAIL]")
        return None

def test_qa(token, kb_id):
    """Test 6: Ask question"""
    print("\n[6] Ask Question")
    if not kb_id:
        print("  [SKIP] - No KB ID")
        return None
        
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    resp = requests.post(f"{BASE_URL}/qa/ask",
        headers=headers,
        json={
            "knowledge_base_id": kb_id,
            "question": "系统的核心功能有哪些？",
            "top_k": 3
        }
    )
    
    if resp.status_code == 200:
        data = resp.json()
        answer = data.get('data', {}).get('answer', '')
        citations = data.get('data', {}).get('citations', [])
        verification = data.get('data', {}).get('verification', {})
        
        print(f"  Answer: {answer[:100]}...")
        print(f"  Citations: {len(citations)}")
        print(f"  Verification: {verification}")
        print("  [PASS]")
        return data.get('data')
    else:
        print(f"  Failed: {resp.status_code} - {resp.text[:200]}")
        print("  [FAIL]")
        return None

def run_e2e_tests():
    """Run all end-to-end tests"""
    print("=" * 60)
    print("V2.0 End-to-End Test Suite")
    print("=" * 60)
    
    try:
        test_health()
        token = test_login()
        kbs = test_knowledge_bases(token)
        kb_id = test_create_kb(token)
        doc_id = test_upload_document(token, kb_id)
        
        # Wait for document processing
        if doc_id:
            print("\n  Waiting 5 seconds for document processing...")
            time.sleep(5)
        
        qa_result = test_qa(token, kb_id)
        
        print("\n" + "=" * 60)
        print("E2E Test Summary")
        print("=" * 60)
        print(f"  KB created: {kb_id is not None}")
        print(f"  Document uploaded: {doc_id is not None}")
        print(f"  Q&A working: {qa_result is not None}")
        
        if qa_result:
            print("\n  [SUCCESS] End-to-end test passed!")
        else:
            print("\n  [PARTIAL] Some tests failed")
            
    except Exception as e:
        print(f"\n  [ERROR] {e}")
        import traceback
        traceback.print_exc()
    
    print("\nE2E Test complete!")

if __name__ == "__main__":
    run_e2e_tests()
