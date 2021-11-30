import tkinter as tk
import tkinter.ttk as ttk
import json
import logging
import os

from palette import palette

pal = palette(path=r"E:\test\other\colors")

from PIL import Image, ImageTk

# from ohsome2label.config import Config, Parser, workspace


# log = logging.getLogger(__name__)


def draw_box():
    pass


def draw_mask():
    pass


def draw_mask():
    pass


class COCO:
    def __init__(self, path):
        self.imgs, self.annos, self.cates = self.parse_coco(path)
        self.cur_img = 0

    def parse_coco(self, path):
        with open(path, "r", encoding="utf-8") as f:
            coco = json.load(f)
            imgs = coco["images"]
            _annos = coco["annotations"]
            cates = coco["categories"]

            # img_list format is {img_id: (file_name, width, height)}
            img_list = {
                _["id"]: (_["file_name"], _["width"], _["height"]) for _ in imgs
            }
            annos = {}
            for anno in _annos:
                if anno["image_id"] in annos:
                    annos[anno["image_id"]][anno["id"]] = anno
                else:
                    annos[anno["image_id"]] = {anno["id"]: anno}
            # for anno in _annos:
            #     if anno["image_id"] in annos:
            #         annos[anno["image_id"]].append({anno["id"]: anno})
            #     else:
            #         annos[anno["image_id"]] = [{anno["id"]: anno}]

            category_list = {cate["id"]: cate["name"] for cate in cates}
            return img_list, annos, category_list

    def get_annos(self, img_id):
        return self.annos.get(img_id)

    def get_anno(self, img_id, anno_id):
        return self.annos.get(img_id).get(anno_id)

    def get_anno_draw(self, img_id, anno_id):
        anno = self.get_anno(img_id, anno_id)
        coords = anno["segmentation"]
        _bbox = anno["bbox"]
        bbox = [_bbox[0], _bbox[1], _bbox[0] + _bbox[2], _bbox[1] + _bbox[3]]
        label = self.cates[anno["category_id"]]
        color = pal.color(label)
        return coords, bbox, label, color

    def get_brief_annos(self, img_id):
        annos = self.annos.get(img_id)
        return [
            (aid, self.get_cate_name(anno["category_id"]))
            for aid, anno in annos.items()
        ]

    def get_cates(self, img_id):
        annos = self.annos.get(img_id)
        cate_ids = set(anno["category_id"] for _, anno in annos.items())
        return [(id, self.get_cate_name(id)) for id in cate_ids]

    def get_cate_name(self, cate_id):
        return self.cates.get(cate_id)

    def get_cate_id(self, cate_name):
        _ = {v: k for k, v in self.cates.items()}
        return _.get(cate_name)


def get_image_list(coco):
    return coco["images"]


def get_image(coco):
    return


class ListPanedWindow(ttk.PanedWindow):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(side=tk.RIGHT, fill=tk.Y)

        self.image_frame = ttk.Frame()
        self.category_frame = ttk.Frame()
        self.anno_frame = ttk.Frame()

        self.image_lb = tk.Listbox(
            self.image_frame, bg="white", selectmode=tk.SINGLE, exportselection=False
        )
        self.category_lb = tk.Listbox(
            self.category_frame,
            bg="white",
            selectmode=tk.EXTENDED,
            exportselection=False,
        )
        self.anno_lb = tk.Listbox(
            self.anno_frame, bg="white", selectmode=tk.EXTENDED, exportselection=False
        )

        # pack all label and sub panel
        ttk.Label(self.image_frame, text="images").pack()
        self.image_lb.pack(fill=tk.BOTH, expand=True)
        ttk.Label(self.category_frame, text="categories").pack()
        self.category_lb.pack(fill=tk.BOTH, expand=True)
        ttk.Label(self.anno_frame, text="annotations").pack()
        self.anno_lb.pack(fill=tk.BOTH, expand=True)
        self.button_frame = ttk.Frame(parent)

        # add button
        self.zoom_button = tk.Button(self.button_frame, text="Zoom In", bg="white")
        self.prev_button = tk.Button(self.button_frame, text="<<", bg="white")
        self.next_button = tk.Button(self.button_frame, text=">>", bg="white")
        self.zoom_button.pack(side=tk.LEFT, padx=10, pady=3)
        self.next_button.pack(side=tk.RIGHT, padx=10, pady=3)
        self.prev_button.pack(side=tk.RIGHT, padx=10, pady=3)

        self.add(self.image_frame)
        self.add(self.anno_frame)
        self.add(self.category_frame)
        self.add(self.button_frame)


class AnnoCanvas(tk.Canvas):
    def __init__(self, parent):
        super().__init__(parent, width=256, height=256, bg="white")
        self.pack()

    def draw_image(self, path, zoom=1):
        zoom = 1 if zoom < 1 else zoom
        _img = Image.open(path).convert("RGBA")
        _img = _img.resize((_img.width * zoom, _img.height * zoom))

        self.img = ImageTk.PhotoImage(_img)
        # self.img = tk.PhotoImage(_img)
        self.create_image(0, 0, image=self.img, anchor=tk.NW)

    def draw_mask(self, coords, color, zoom=1):
        coords = [[_ * zoom for _ in _c] for _c in coords]
        self.create_polygon(coords, fill=color)

    def draw_bbox(self, bbox, color, zoom=1):
        bbox = [_ * zoom for _ in bbox]
        self.create_rectangle(bbox, outline=color)

    # def draw_label(self, label, bbox, color):
    #     self.create_text(bbox[0], bbox[1], text=label, fill=color)

    def zoom_in(self):
        pass

    def zoom_out(self):
        pass

    def resize(self):
        pass

    def update_image(self):
        pass


class Viewer:
    def __init__(self, parent, coco_obj: COCO):
        self.parent = parent
        self.coco = coco_obj
        self.zoom = 1
        self.cur_img = 0
        self.list_pw = ListPanedWindow(self.parent)
        self.cvframe = ttk.Frame(self.parent, height=512, width=512)
        self.anno_canvas = AnnoCanvas(self.cvframe)
        self.cvframe.pack(fill=tk.X)

        self.img_list = self.coco.imgs
        self.anno_list = self.coco.annos
        self.list_pw.image_lb.insert(
            tk.END, *[self.img_list[_][0] for _ in self.img_list]
        )

        self.list_pw.image_lb.select_set(0)
        self.update_img(self.cur_img)

        self.bind_event()

    def onclick(self, event):
        pass

    def select_anno(self, _):
        self.list_pw.category_lb.select_clear(0, tk.END)

        cur_cates = set()
        aids = []
        for i in self.list_pw.anno_lb.curselection():
            aids.append(self.list_pw.anno_lb.get(i)[0])
            cur_cates.add(self.list_pw.anno_lb.get(i)[1])

        cur_cates = list(cur_cates)
        cates = [self.coco.get_cate_id(cate) for cate in cur_cates]
        cate_lb = self.list_pw.category_lb.get(0, tk.END)
        for cate in cates:
            for idx, item in enumerate(cate_lb):
                if cate in item:
                    self.list_pw.category_lb.select_set(idx)

        img_name = self.list_pw.image_lb.get(self.cur_img)
        for id, item in self.img_list.items():
            if img_name == item[0]:
                img_id = id
                continue
        annos = self.coco.get_brief_annos(img_id)
        self.update_annos(aids, annos, img_id)

    def select_cate(self, _):
        self.list_pw.anno_lb.select_clear(0, tk.END)

        cur_cates = []
        for i in self.list_pw.category_lb.curselection():
            cur_cates.append(self.list_pw.category_lb.get(i)[1])
        anno_lb = self.list_pw.anno_lb.get(0, tk.END)
        aids = []
        for cate in cur_cates:
            for idx, item in enumerate(anno_lb):
                if cate in item:
                    aids.append(item[0])
                    self.list_pw.anno_lb.select_set(idx)

        img_name = self.list_pw.image_lb.get(idx)
        img_id = -1
        for id, item in self.img_list.items():
            if img_name == item[0]:
                img_id = id
        # img_id = self.list_pw.image_lb.get(self.cur_img)
        annos = self.coco.get_brief_annos(img_id)
        self.update_annos(aids, annos, self.cur_img)

    def next_img(self, _):
        self.list_pw.image_lb.select_clear(0, tk.END)
        if self.cur_img + 1 < self.list_pw.image_lb.size():
            self.cur_img += 1
        else:
            self.cur_img = 0

        self.list_pw.image_lb.select_set(self.cur_img)
        self.list_pw.image_lb.see(self.cur_img)
        self.update_img(self.cur_img)

    def prev_img(self, _):
        self.list_pw.image_lb.select_clear(0, tk.END)
        if self.cur_img - 1 > 0:
            self.cur_img -= 1
        else:
            self.cur_img = self.list_pw.image_lb.size() - 1
        self.list_pw.image_lb.select_set(self.cur_img)
        self.list_pw.image_lb.see(self.cur_img)
        self.update_img(self.cur_img)

    def select_img(self, _):
        self.cur_img = self.list_pw.image_lb.curselection()[0]

        self.update_img(self.cur_img)

    def update_img(self, idx):

        # img_id = self.list_pw.image_lb.get(idx)
        img_name = self.list_pw.image_lb.get(idx)
        img_id = -1
        for id, item in self.img_list.items():
            if img_name == item[0]:
                img_id = id
        annos = self.coco.get_brief_annos(img_id)
        self.list_pw.anno_lb.delete(0, tk.END)
        self.list_pw.anno_lb.insert(tk.END, *annos)
        self.list_pw.anno_lb.select_set(0, tk.END)

        cates = self.coco.get_cates(img_id)
        self.list_pw.category_lb.delete(0, tk.END)
        self.list_pw.category_lb.insert(tk.END, *cates)
        self.list_pw.category_lb.select_set(0, tk.END)
        aids = [_[0] for _ in annos]

        self.update_annos(aids, annos, img_id)
        self.zoom = 1 if self.zoom < 1 else self.zoom

    def update_annos(self, aids, annos, img_id):
        # self.anno_canvas.delete(tk.ALL)
        _path = os.path.join(img_path, self.coco.imgs[img_id][0])
        self.anno_canvas.draw_image(_path, self.zoom)
        for aid in aids:
            coords, bbox, label, color = self.coco.get_anno_draw(img_id, aid)
            self.anno_canvas.draw_mask(coords, color, self.zoom)
            self.anno_canvas.draw_bbox(bbox, color, self.zoom)
            # self.anno_canvas.draw_label(label, bbox, color)

    def zoom_in(self, _):
        if self.zoom == 1:
            self.zoom = 2
            self.list_pw.zoom_button.config(text="Zoom Out")
        else:
            self.zoom = 1 / 2
            self.list_pw.zoom_button.config(text="Zoom In")
        w = int(self.anno_canvas["width"])
        h = int(self.anno_canvas["height"])
        self.anno_canvas.config(width=self.zoom * w, height=self.zoom * h)
        self.update_img(self.cur_img)

    def bind_event(self):
        self.list_pw.image_lb.bind("<<ListboxSelect>>", self.select_img)
        self.list_pw.anno_lb.bind("<<ListboxSelect>>", self.select_anno)
        self.list_pw.category_lb.bind("<<ListboxSelect>>", self.select_cate)
        # self.anno_canvas.bind("<Button-1>", self.onclick)
        self.parent.bind("<Right>", self.next_img)
        self.parent.bind("<Left>", self.prev_img)
        self.list_pw.next_button.bind("<Button-1>", self.next_img)
        self.list_pw.prev_button.bind("<Button-1>", self.prev_img)
        self.list_pw.zoom_button.bind("<Button-1>", self.zoom_in)


img_path = "E:\\test\\images"


def main():
    root = tk.Tk()
    root.title("Ohsome2label Viewer")
    coco_obj = COCO(r"E:/test/annotations/geococo.json")
    viewer = Viewer(root, coco_obj)
    # root.resizable(False, False)
    root.mainloop()


if __name__ == "__main__":
    main()
