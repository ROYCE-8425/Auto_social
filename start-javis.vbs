' ============================================
'  Javis OS - chạy NGẦM (ẩn cửa sổ cmd)
'  Double-click file này (hoặc start-javis.bat) để bật server ở chế độ nền.
'  Log ghi vào server\javis.log. Dừng bằng stop-javis.bat.
' ============================================
Set fso = CreateObject("Scripting.FileSystemObject")
Set rootFolder = fso.GetFolder(fso.GetParentFolderName(WScript.ScriptFullName))
root = rootFolder.ShortPath
If root = "" Then root = rootFolder.Path
Set sh = CreateObject("WScript.Shell")

' QUAN TRỌNG: mọi lệnh đều cd /d vào root trước - KHÔNG dựa vào working directory
' kế thừa (CurrentDirectory không đáng tin tuỳ nơi gọi, từng làm bước stop chết
' im lặng với lỗi 'stop-javis.bat is not recognized').

' Tắt instance cũ trước (ẩn, chờ xong). Output ghi server\stop-last.log để soi khi trục trặc.
' GỌI BẰNG ĐƯỜNG DẪN TUYỆT ĐỐI: tên trần "stop-javis.bat" bị cmd từ chối tìm theo thư mục
' hiện tại khi môi trường có NoDefaultCurrentDirectoryInExePath (đường dẫn có "\" thì không sao).
sh.Run "cmd /c cd /d """ & root & """ && call """ & root & "\stop-javis.bat"" > server\stop-last.log 2>&1", 0, True

' Chạy server ẩn (0 = cửa sổ ẩn, False = không chờ). Output -> server\javis.log
sh.Run "cmd /c cd /d """ & root & """ && .venv\Scripts\python.exe server\main.py > server\javis.log 2>&1", 0, False
