import json
from pathlib import Path
import re

def parse_testcase_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split sections using regex
    sections = re.split(r'^##', content, flags=re.MULTILINE)
    
    data = {
        'system_prompt': '',
        'fact_set': '',
        'questions': []
    }
    
    for section in sections:
        if not section.strip():
            continue
            
        header, *body = section.strip().split('\n', 1)
        body = body[0] if body else ''
        
        if header.startswith('SYSTEM_PROMPT'):
            data['system_prompt'] = ' '.join(body.strip().splitlines())
        elif header.startswith('FACT_SET'):
            data['fact_set'] = ' '.join(body.strip().splitlines())
        elif header.startswith('QUESTIONS'):
            questions = re.split(r'^#QID:', body, flags=re.MULTILINE)
            for q in questions[1:]:  # Skip first empty split
                q_data = {}
                lines = q.strip().split('\n')
                q_data['id'] = lines[0].strip()
                for line in lines[1:]:
                    if line.startswith('#TYPE:'):
                        q_data['question_type'] = line.split(':', 1)[1].strip()
                    elif line.startswith('#QUESTION:'):
                        q_data['question'] = line.split(':', 1)[1].strip()
                    elif line.startswith('#ANSWER:'):
                        q_data['expected_answer'] = line.split(':', 1)[1].strip()
                data['questions'].append(q_data)
    
    return data

def convert_directory(input_folder, output_folder):
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    output_path.mkdir(exist_ok=True)
    
    for txt_file in input_path.rglob('*.txt'):
        # Create matching JSON path in output folder
        relative_path = txt_file.relative_to(input_path)
        json_path = output_path / relative_path.with_suffix('.json')
        
        # Create parent directories if needed
        json_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Parse and save as individual JSON file
        testcase_data = parse_testcase_file(txt_file)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(testcase_data, f, indent=2, ensure_ascii=False)

    print(f"Converted {sum(1 for _ in input_path.rglob('*.txt'))} test cases")

if __name__ == "__main__":
    convert_directory('raw_testcases', 'processed_testcases')
