"""Compile candidate annotations into one sorted UTF-8 blob for Lua binary search."""
import hashlib

HEADER='# booru-annotations-v1\t'

def match_key(tag,code):
    return f'M:{len(tag.encode("utf-8"))}:{tag}:{code}'

def write_annotations(rows,source,target):
    labels={}
    records={}
    for row in rows:
        tag,zh,code=row['tag'],row['zh'],row['code']
        role=row.get('role') or ('alias' if tag.startswith('__prompt__:') else 'primary')
        text=tag.removeprefix('__prompt__:')
        records[match_key(tag,code)]=(zh,role=='primary')
        level=(2 if role=='primary' else 0)+(0 if '〔俗称' in zh else 1)
        priority=(level,int(row['weight']))
        if text not in labels or priority>labels[text][0]:
            labels[text]=(priority,zh)
    records.update({'L:'+text:(value[1],False) for text,value in labels.items()})
    header=HEADER+hashlib.sha256(source.read_bytes()).hexdigest()+'\n'
    target.write_bytes((header+''.join(key+'\t'+zh+'\t'+str(int(primary))+'\n'
                                     for key,(zh,primary) in sorted(records.items()))).encode('utf-8'))
