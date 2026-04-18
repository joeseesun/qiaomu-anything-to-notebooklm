#!/usr/bin/env python3
"""
通过 Get笔记 API 获取播客/音频/视频的完整转写文本。
支持小宇宙、喜马拉雅、B站视频等音频/视频平台。

用法: python3 get_podcast_transcript.py <podcast_or_video_url>
输出: JSON { txt_path, title, content_length, note_id, source_url }
"""

import subprocess, json, os, sys, time, tempfile, re

TOKENS_FILE = os.path.expanduser('~/.claude/skills/getnote/tokens.json')

def getnote_request(method, path, body=None):
    api_key = os.environ.get('GETNOTE_API_KEY')
    client_id = os.environ.get('GETNOTE_CLIENT_ID')
    if not api_key or not client_id:
        print("ERROR: GETNOTE_API_KEY or GETNOTE_CLIENT_ID not set", file=sys.stderr)
        sys.exit(1)
    url = f'https://openapi.biji.com{path}'
    cmd = ['curl', '-s', '-X', method, url,
           '-H', f'Authorization: {api_key}',
           '-H', f'X-Client-ID: {client_id}']
    if body:
        cmd += ['-H', 'Content-Type: application/json', '-d', json.dumps(body)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(r.stdout)

def load_tokens():
    if not os.path.exists(TOKENS_FILE):
        print(f"ERROR: Token file not found: {TOKENS_FILE}", file=sys.stderr)
        sys.exit(1)
    with open(TOKENS_FILE) as f:
        return json.load(f)

def save_tokens(tokens):
    with open(TOKENS_FILE, 'w') as f:
        json.dump(tokens, f, indent=2)

def refresh_jwt(refresh_token):
    cmd = ['curl', '-s', '-X', 'POST',
           'https://notes-api.biji.com/account/v2/web/user/auth/refresh',
           '-H', 'Content-Type: application/json',
           '-H', 'Origin: https://www.biji.com',
           '-H', 'Referer: https://www.biji.com/',
           '-d', json.dumps({'refresh_token': refresh_token})]
    r = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(r.stdout)
    if data.get('h', {}).get('c') != 0:
        raise RuntimeError(f"Token refresh failed: {data}")
    return data['c']['token']

def get_valid_jwt():
    tokens = load_tokens()
    now = int(time.time())
    if now >= tokens.get('refresh_token_expire_at', 0):
        print("ERROR: refresh_token expired (90 days). Re-initialize from browser.", file=sys.stderr)
        sys.exit(1)
    if now >= tokens.get('token_expire_at', 0) - 300:
        print("Refreshing JWT...", file=sys.stderr)
        new_info = refresh_jwt(tokens['refresh_token'])
        tokens.update({
            'token': new_info['token'],
            'token_expire_at': new_info['token_expire_at'],
            'refresh_token': new_info.get('refresh_token', tokens['refresh_token']),
            'refresh_token_expire_at': new_info.get('refresh_token_expire_at', tokens['refresh_token_expire_at']),
        })
        save_tokens(tokens)
    return tokens['token']

def get_note_transcript(note_id):
    jwt = get_valid_jwt()
    url = f'https://get-notes.luojilab.com/voicenotes/web/notes/{note_id}/links/detail'
    cmd = ['curl', '-s', url,
           '-H', f'Authorization: Bearer {jwt}',
           '-H', 'Content-Type: application/json',
           '-H', 'Origin: https://www.biji.com',
           '-H', 'Referer: https://www.biji.com/']
    r = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(r.stdout)
    if data.get('h', {}).get('c') == 0:
        return data['c']
    raise RuntimeError(f"Transcript fetch failed: {data}")

def main():
    if len(sys.argv) < 2:
        print("Usage: get_podcast_transcript.py <podcast_url>", file=sys.stderr)
        sys.exit(1)

    podcast_url = sys.argv[1]
    print(f"Podcast URL: {podcast_url}", file=sys.stderr)

    # Step 1: Create link note via OpenAPI
    print("Creating link note via Get笔记...", file=sys.stderr)
    resp = getnote_request('POST', '/open/api/v1/resource/note/save', {
        'note_type': 'link',
        'link_url': podcast_url
    })

    if not resp.get('success'):
        print(f"ERROR: Failed to create note: {json.dumps(resp, ensure_ascii=False)}", file=sys.stderr)
        sys.exit(1)

    tasks = resp.get('data', {}).get('tasks', [])
    if not tasks:
        print("ERROR: No tasks returned", file=sys.stderr)
        sys.exit(1)

    task_id = tasks[0]['task_id']
    print(f"Task created: {task_id}", file=sys.stderr)

    # Step 2: Wait for transcription
    print("Waiting for transcription...", file=sys.stderr)
    note_id = None
    for i in range(40):
        time.sleep(30)
        prog = getnote_request('POST', '/open/api/v1/resource/note/task/progress',
                               body={'task_id': task_id})
        task_status = prog['data']['status']
        print(f"[{i+1}] status={task_status}", file=sys.stderr)
        if task_status == 'success':
            note_id = prog['data']['note_id']
            break
        if task_status == 'failed':
            print("ERROR: Transcription failed", file=sys.stderr)
            sys.exit(1)

    if not note_id:
        print("ERROR: Transcription timed out", file=sys.stderr)
        sys.exit(1)

    # Step 3: Get full transcript via Web API
    print(f"Fetching transcript for note_id={note_id}...", file=sys.stderr)
    result = get_note_transcript(str(note_id))
    title = result.get('title', '未知标题')
    content = result.get('content', '')
    orig_title = result.get('web_title', title)

    if not content:
        print("ERROR: No transcript content returned", file=sys.stderr)
        sys.exit(1)

    # Step 4: Save as TXT
    safe_title = re.sub(r'[：:/\\?|<>*"\']', '_', orig_title or title).strip('_')[:80]
    txt_path = tempfile.mktemp(suffix='.txt', prefix=f'podcast_{safe_title}_')

    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(f"# {orig_title or title}\n\n")
        f.write(f"来源: {podcast_url}\n")
        f.write(f"笔记ID: {note_id}\n")
        f.write(f"获取时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n")
        f.write(content)

    # Output JSON result
    output = {
        "txt_path": txt_path,
        "title": orig_title or title,
        "content_length": len(content),
        "note_id": str(note_id),
        "source_url": podcast_url
    }
    print(json.dumps(output, ensure_ascii=False))
    print(f"Transcript saved: {txt_path} ({len(content)} chars)", file=sys.stderr)

if __name__ == '__main__':
    main()
