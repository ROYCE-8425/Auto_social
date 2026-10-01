import re

path = 'ops/src/pages/Tasks.tsx'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace newAssignee initial state
content = content.replace("const [newAssignee, setNewAssignee] = useState<string>('NV')", "const [newAssignee, setNewAssignee] = useState<string>('nv_an')")

# Refine handleCreateTask find logic
old_find = "const selectedStaffObj = staffList.find((s) => s.code === newAssignee) || staffList[1]"
new_find = """const selectedStaffObj = staffList.find((s) => (s.username === newAssignee || s.code === newAssignee)) || staffList[2]"""
if old_find in content:
    content = content.replace(old_find, new_find)

# Refine assignee object creation
old_assignee = """      assignee: {
        code: selectedStaffObj.code,
        name: selectedStaffObj.name,
        bg: selectedStaffObj.bg || 'bg-slate-800 text-white',
      },"""
new_assignee = """      assignee: {
        code: selectedStaffObj.code,
        name: selectedStaffObj.name,
        username: selectedStaffObj.username,
        bg: selectedStaffObj.bg || 'bg-slate-800 text-white',
      },"""
if old_assignee in content:
    content = content.replace(old_assignee, new_assignee)

# Refine top staff filter dropdown
old_select = """              {staffList.map((s) => (
                <option key={s.code} value={s.code}>
                  {s.name}
                </option>
              ))}"""
new_select = """              {staffList.map((s) => {
                const val = s.username || s.code
                return (
                  <option key={val} value={val}>
                    {s.name}
                  </option>
                )
              })}"""
if old_select in content:
    content = content.replace(old_select, new_select)

# Refine modal select dropdown
old_modal_select = """                    <option value="NV">Nguyễn Văn (NV)</option>
                    <option value="LT">Lê Tuấn (LT)</option>
                    <option value="TH">Trần Hùng (TH)</option>
                    <option value="TM">Trần Minh (TM)</option>"""
new_modal_select = """                    {staffList
                      .filter((s) => s.code !== 'all' && s.code !== 'my_tasks')
                      .map((s) => {
                        const val = s.username || s.code
                        return (
                          <option key={val} value={val}>
                            {s.name} ({s.code})
                          </option>
                        )
                      })}"""
if old_modal_select in content:
    content = content.replace(old_modal_select, new_modal_select)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Tasks.tsx updated with refined assignee and dropdowns.")
