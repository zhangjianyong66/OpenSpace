#!/usr/bin/env python3
"""
QQ邮箱IMAP邮件读取器
用于读取指定主题的邮件内容
"""

import imaplib
import email
from email.header import decode_header
import re
import html

def decode_str(s):
    """解码邮件头"""
    if s is None:
        return ""
    decoded = decode_header(s)
    value = ""
    for part, charset in decoded:
        if isinstance(part, bytes):
            try:
                value += part.decode(charset or 'utf-8', errors='replace')
            except:
                value += part.decode('utf-8', errors='replace')
        else:
            value += part
    return value

def get_email_body(msg):
    """提取邮件正文内容"""
    body = ""
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))
            
            # 跳过附件
            if "attachment" in content_disposition:
                continue
            
            # 优先获取纯文本内容
            if content_type == "text/plain":
                try:
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset() or 'utf-8'
                    body = payload.decode(charset, errors='replace')
                    break
                except:
                    pass
            # 如果没有纯文本，获取HTML内容
            elif content_type == "text/html" and not body:
                try:
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset() or 'utf-8'
                    html_body = payload.decode(charset, errors='replace')
                    # 简单的HTML到文本转换
                    body = html_to_text(html_body)
                except:
                    pass
    else:
        # 非多部分邮件
        try:
            payload = msg.get_payload(decode=True)
            charset = msg.get_content_charset() or 'utf-8'
            content_type = msg.get_content_type()
            
            if content_type == "text/html":
                body = html_to_text(payload.decode(charset, errors='replace'))
            else:
                body = payload.decode(charset, errors='replace')
        except:
            body = str(msg.get_payload())
    
    return body

def html_to_text(html_content):
    """将HTML内容转换为纯文本"""
    # 移除script和style标签
    text = re.sub(r'<(script|style).*?>.*?</\1>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    # 将<br>, <p>等标签转换为换行
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</p>', '\n\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<p>', '', text, flags=re.IGNORECASE)
    # 移除所有HTML标签
    text = re.sub(r'<[^>]+>', '', text)
    # 解码HTML实体
    text = html.unescape(text)
    # 清理多余空白
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

def connect_qq_imap(email_address, password):
    """连接QQ邮箱IMAP服务器"""
    # QQ邮箱IMAP服务器设置
    imap_server = "imap.qq.com"
    imap_port = 993
    
    try:
        # 创建SSL连接
        mail = imaplib.IMAP4_SSL(imap_server, imap_port)
        # 登录
        mail.login(email_address, password)
        print(f"成功登录邮箱: {email_address}")
        return mail
    except Exception as e:
        print(f"登录失败: {e}")
        return None

def search_emails_by_subject(mail, subject_keywords):
    """搜索包含指定关键词的邮件"""
    try:
        # 选择收件箱
        mail.select("INBOX")
        
        # 搜索所有邮件
        _, message_numbers = mail.search(None, "ALL")
        
        matching_emails = []
        email_ids = message_numbers[0].split()
        
        # 从最新的邮件开始遍历
        for email_id in reversed(email_ids):
            _, msg_data = mail.fetch(email_id, "(RFC822)")
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # 获取邮件主题
            subject = decode_str(msg["Subject"])
            
            # 检查是否匹配任一关键词
            for keyword in subject_keywords:
                if keyword.lower() in subject.lower():
                    matching_emails.append({
                        'id': email_id,
                        'subject': subject,
                        'from': decode_str(msg["From"]),
                        'date': decode_str(msg["Date"]),
                        'body': get_email_body(msg)
                    })
                    break
            
            # 如果找到足够的邮件就停止
            if len(matching_emails) >= len(subject_keywords):
                break
        
        return matching_emails
    except Exception as e:
        print(f"搜索邮件失败: {e}")
        return []

def main():
    # 邮箱配置 - 请替换为您的QQ邮箱授权码
    # QQ邮箱需要使用授权码而不是密码
    # 获取方式: QQ邮箱设置 -> 账户 -> 开启IMAP服务 -> 生成授权码
    email_address = "605600162@qq.com"
    
    # 从环境变量或用户输入获取授权码
    import os
    auth_code = os.environ.get("QQ_EMAIL_AUTH_CODE")
    
    if not auth_code:
        print("请设置QQ邮箱授权码环境变量: export QQ_EMAIL_AUTH_CODE='your_auth_code'")
        print("或者直接在脚本中设置auth_code变量")
        # 这里可以让用户输入
        auth_code = input("请输入QQ邮箱授权码: ").strip()
    
    # 要搜索的邮件主题关键词
    subject_keywords = [
        "See Gemini 3.1 Pro handle real engineering work (live)",
        "[Cursor - Community Forum] Summary"
    ]
    
    # 连接邮箱
    mail = connect_qq_imap(email_address, auth_code)
    if not mail:
        return
    
    try:
        # 搜索邮件
        print(f"\n搜索邮件主题包含以下关键词的邮件:")
        for kw in subject_keywords:
            print(f"  - {kw}")
        print()
        
        emails = search_emails_by_subject(mail, subject_keywords)
        
        # 显示结果
        if emails:
            print(f"找到 {len(emails)} 封匹配的邮件:\n")
            print("=" * 80)
            
            for i, email_info in enumerate(emails, 1):
                print(f"\n【邮件 {i}】")
                print(f"主题: {email_info['subject']}")
                print(f"发件人: {email_info['from']}")
                print(f"日期: {email_info['date']}")
                print(f"\n{'='*40} 正文内容 {'='*40}")
                print(email_info['body'])
                print(f"\n{'='*80}")
        else:
            print("未找到匹配的邮件")
            
            # 列出最近的10封邮件主题供参考
            print("\n最近的10封邮件主题:")
            mail.select("INBOX")
            _, message_numbers = mail.search(None, "ALL")
            email_ids = message_numbers[0].split()
            for email_id in reversed(email_ids[-10:]):
                _, msg_data = mail.fetch(email_id, "(RFC822)")
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                subject = decode_str(msg["Subject"])
                print(f"  - {subject}")
    
    finally:
        # 关闭连接
        mail.close()
        mail.logout()
        print("\n已断开邮箱连接")

if __name__ == "__main__":
    main()
