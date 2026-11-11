"""Kiểm thử kịch bản chatbot:  python3 -m unittest chatbot.test_engine -v  (chạy từ thư mục lia-casa-10-ty)"""
import unittest

from chatbot.engine import Bot, as_plain_text

bot = Bot()


def say(text, state, payload=None):
    return bot.handle(text, state, payload=payload, name="Lan")


class TestEngine(unittest.TestCase):
    def test_chao_co_menu(self):
        r = say("hi shop", {})
        self.assertIn("Lan", r[0].text)
        self.assertEqual(len(r[0].options), 5)

    def test_hoi_gia_hang_co_san_lay_dung_gia(self):
        r = say("sofa milano giá bao nhiêu vậy", {})
        self.assertIn("39.900.000 đ", r[0].text)
        self.assertIn("45.900.000 đ", r[0].text)

    def test_hang_cap_nhat_sau_khong_bia_gia(self):
        r = say("cho hỏi giá sofa Firenze", {})
        self.assertIn("lô nhập", r[0].text)
        self.assertIn("68.000.000 đ", r[0].text)  # chỉ nêu "dự kiến từ" có trong catalog
        self.assertIn("SĐT", r[0].text)

    def test_ghe_khong_bi_nham_showroom(self):
        r = say("có mẫu ghế nào không", {})
        self.assertIn("Bergen", r[0].text)

    def test_danh_muc_va_chon_so_kieu_zalo(self):
        st = {}
        r = say("phòng ăn", st)
        self.assertIn("Valencia", r[0].text)
        self.assertIn("1.", as_plain_text(r[0]))
        r = say("1", st)  # gõ số chọn mẫu đầu tiên
        self.assertIn("32.500.000 đ", r[0].text)
        self.assertEqual(st["sku"], "LC-BA-001")

    def test_xin_sdt_tao_lead(self):
        st = {}
        say("giá giường roma", st)
        r = say("số mình 0912 345 678 nhé", st)
        self.assertIn("đã nhận", r[0].text)
        self.assertEqual(st["lead"]["sdt"], "0912345678")
        self.assertEqual(st["lead"]["sku"], "LC-GN-001")

    def test_thiet_ke_ngan_sach_cao_la_lead_nong(self):
        st = {}
        say("mình cần thiết kế full nhà biệt thự", st)
        say("khoảng 250m2", st)
        say("", st, payload="ngan_sach:Trên 200 triệu")
        say("+84 912345678", st)
        self.assertEqual(st["lead"]["tag"], "nong")
        self.assertEqual(st["lead"]["dien_tich"], "khoảng 250m2")
        self.assertEqual(st["lead"]["sdt"], "0912345678")

    def test_faq_bao_hanh(self):
        r = say("bảo hành mấy năm vậy", {})
        self.assertIn("bảo hành", r[0].text.lower())

    def test_gap_nhan_vien_thi_bot_im(self):
        st = {}
        say("cho mình gặp nhân viên", st)
        self.assertTrue(st["handoff"])
        self.assertEqual(say("alo", st), [])


if __name__ == "__main__":
    unittest.main()
