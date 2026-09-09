---
name: "Kiểm tra goal đăng bài Facebook"
description: "Kiểm tra goal Facebook vừa chạy: thời gian, token, post_id, ảnh đã dùng và lỗi sai khóa học."
group: "Facebook"
origin: javis-learned
status: active
created: 2026-09-08
---
## Khi nào dùng

Dùng khi người dùng yêu cầu kiểm tra một goal hoặc task đăng bài Facebook vừa hoàn thành.

Dùng khi cần xác minh bài vừa đăng có đúng khóa học, đúng ảnh, đúng số lượng ảnh và mức tiêu hao token/thời gian hay không.

Dùng sau khi vừa deploy hoặc sửa workflow đăng bài Facebook để kiểm tra bản mới chạy thật như thế nào.

## Chuẩn bị

Xác định task hoặc goal mới nhất liên quan đến workflow đăng bài Facebook.

Ưu tiên dữ liệu thật từ task log, loop log, usage-events, post_id, payload đăng bài và thư mục ảnh đã chuẩn hóa.

Nếu có file đính kèm từ người dùng, chỉ đọc để lấy bối cảnh, không lưu vào sources trừ khi người dùng yêu cầu rõ.

## Cách chạy

Đọc trạng thái task/goal mới nhất để lấy thời điểm bắt đầu, hoàn tất, route, workflow, post_id và summary.

Đọc usage-events gần thời điểm task chạy để tính input token, output token và tổng token.

Đọc log loop hoặc Kanban để đối chiếu thời gian chạy và kết quả cuối.

Tìm payload hoặc manifest của bài đăng nếu có để biết khóa học, caption, danh sách ảnh gốc và ảnh đã normalize.

Kiểm tra thư mục album_ready hoặc thư mục ảnh output mới nhất, nhưng phải chú ý album_ready có thể bị ghi đè bởi bài sau.

Nếu cần xác minh bằng mắt, mở các ảnh nghi ngờ và đối chiếu nội dung ảnh với khóa học trong caption/task.

## Quy trình

1. Chốt goal/task mới nhất bằng timestamp và route, không đoán theo cảm giác.

2. Tính thời gian chạy từ started_at đến finished_at hoặc từ log tương đương.

3. Lấy token từ usage-events đúng khoảng thời gian, tách input và output nếu có.

4. Lấy post_id và trạng thái đăng nếu log có trả về.

5. Đối chiếu khóa học trong task/caption với ảnh đã dùng.

6. Kiểm tra số lượng ảnh thực tế, nhất là khi người dùng phản ánh hệ thống dùng quá nhiều ảnh.

7. Nếu phát hiện ảnh sai ngành, ghi rõ ảnh nào sai và sai vì sao.

8. Phân biệt hai kết luận: hiệu năng có cải thiện hay không, và chất lượng nghiệp vụ có đúng hay không.

9. Nếu chưa có bài live sau bản mới, nói rõ chưa thể kết luận bản mới đã sửa xong.

## Bẫy

Không dùng album_ready làm bằng chứng tuyệt đối nếu nó có thể đã bị ghi đè bởi bài đăng sau.

Không kết luận ảnh đúng chỉ vì tên file nằm trong folder đúng khóa học. File có thể bị đặt nhầm thư mục.

Không lấy số token tổng ngày thay cho token của goal nếu có usage-events theo thời điểm.

Không nói bản tối ưu thành công chỉ vì thời gian giảm. Sai ảnh hoặc sai khóa học vẫn là lỗi nghiệp vụ nghiêm trọng.

Không hứa sẽ chờ goal chạy xong rồi báo lại. Nếu chưa có dữ liệu, nói chưa kiểm được hoặc queue task riêng nếu người dùng yêu cầu.

## Kiểm chứng

Báo cáo cuối phải có ít nhất: task_id hoặc post_id, thời gian chạy, tổng token, khóa học, số ảnh, kết luận đúng/sai asset.

Nếu có lỗi, nêu nguyên nhân khả dĩ theo bằng chứng code/log, không suy đoán quá mức.

Nếu chưa chạy bài mới sau bản deploy, ghi rõ bài gần nhất thuộc bản trước hay bản sau.
