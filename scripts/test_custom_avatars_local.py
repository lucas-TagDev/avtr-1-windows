import io
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase, main
from unittest.mock import patch
from PIL import Image
from avtr1_renderer import custom_avatars as store


def photo(size=(600, 1200)):
    data = io.BytesIO()
    Image.new("RGB", size, (255, 0, 0)).save(data, "PNG")
    return data.getvalue()


class Templates(TestCase):
    def test_delete_removes_only_selected_custom_template(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            avatar_id = 'custom_' + 'a'*32
            for suffix in ('.png','.jpg','.json'):
                (root / (avatar_id+suffix)).write_bytes(b'test')
            keep = root / 'keep.png'
            keep.write_bytes(b'keep')
            with patch.object(store, 'directory', return_value=root):
                store.delete_template(avatar_id)
                with self.assertRaises(ValueError):
                    store.delete_template('../keep')
            self.assertEqual(list(root.iterdir()), [keep])

    def test_preserves_portrait_proportions(self):
        image = store.prepare_image(photo())
        self.assertEqual(image.size, (1280, 720))
        self.assertEqual(image.getpixel((640, 0)), (255, 0, 0))
        self.assertEqual(image.getpixel((450, 360)), (28, 31, 38))
        self.assertEqual(image.getpixel((470, 360)), (255, 0, 0))

    def test_bad_photo_and_small_photo_rejected(self):
        for data in (b"not a photo", photo((50, 50))):
            with self.assertRaises(ValueError):
                store.prepare_image(data)

    def test_saved_metadata_and_thumbnail_are_reusable(self):
        with TemporaryDirectory(dir=Path(__file__).resolve().parents[1] / "artifacts") as tmp:
            with patch.object(store, "directory", return_value=Path(tmp)):
                loader = SimpleNamespace(load=lambda path, avatar_id: SimpleNamespace(id=avatar_id))
                item, avatar = store.register(photo(), "  Meu avatar  ", loader)
                self.assertEqual(item["name"], "Meu avatar")
                self.assertEqual(store.templates(), [item])
                self.assertTrue((Path(tmp) / (avatar.id + ".jpg")).is_file())
                self.assertTrue(store.valid_id(avatar.id))
                self.assertFalse(store.valid_id("../escape"))

    def test_failed_registration_does_not_leave_a_template(self):
        with TemporaryDirectory(dir=Path(__file__).resolve().parents[1] / "artifacts") as tmp:
            with patch.object(store, "directory", return_value=Path(tmp)):
                def fail(*args, **kwargs):
                    raise RuntimeError("No face detected")
                with self.assertRaises(RuntimeError):
                    store.register(photo(), "Sem rosto", SimpleNamespace(load=fail))
                self.assertEqual(list(Path(tmp).iterdir()), [])


if __name__ == "__main__":
    main(verbosity=2)
