from typing import Any, Dict, List, Union
import warnings
from PyPDF2 import PdfFileReader, PdfFileWriter
from PyPDF2.generic import Destination, IndirectObject

def _setup_page_id_to_num(pdf, pages=None, _result=None, _num_pages=None):
    if _result is None:
        _result = {}
    if pages is None:
        _num_pages = []
        pages = pdf.trailer["/Root"].getObject()["/Pages"].getObject()
    t = pages["/Type"]
    if t == "/Pages":
        for page in pages["/Kids"]:
            _result[page.idnum] = len(_num_pages)
            _setup_page_id_to_num(pdf, page.getObject(), _result, _num_pages)
    elif t == "/Page":
        _num_pages.append(1)
    return _result


# main
pdfpath = r"D:\下载\《独立成分分析＝INDEPENDENT COMPONENT ANALYSIS》_13569825.pdf"
pdf_in = PdfFileReader(pdfpath)
pdf_out = PdfFileWriter()

# 将读取的pdf放到writer中
pageCount = pdf_in.getNumPages()
print("总页数：", pageCount)
# map page ids to page numbers
pg_id_num_map = _setup_page_id_to_num(pdf_in)
outlines = pdf_in.getOutlines()

pg_num = pg_id_num_map[outlines[0].page.idnum] + 1
print(pg_num)

print(outlines[0])

for iPage in range(pageCount):
    pdf_out.addPage(pdf_in.getPage(iPage))


def add_bookmark(
        pdf_out: PdfFileWriter,
        outlines: Union[List[Union[List[Any], Destination]], Destination],
        page_number_offset: int = 0,
        sep: str = " ",
        sec_sep: str = ".",
        parents: Dict[str, IndirectObject] = dict(),
        parent: IndirectObject = None,
) -> IndirectObject:
    """添加书签，并纠正书签的页码

    Args:
        pdf_out: PdfFileWriter
        outlines: 目录列表或者目录项
        page_number_offset: 页码偏移. Defaults to 0.
        sep: 标题和标题编号之间的分隔符，例子："1.1 第一章第一小节". Defaults to " ".
        sec_sep: 标题等级的分割符，例子："1.1.2". Defaults to ".".
        parent: 目录项的父项.
        parents: 目录项的父项（根据章节编号得到的父项，优先使用）
    Returns:
        IndirectObject: 当前目录项
    """

    # parent0 = pdf_out.addBookmark('父目录', 0, parent=None)  # 添加父目录
    # # 使用方法： addBookmark(书签文字,书签页码,书签的父目录)，返回值是书签（可以作为其他书签的父目录）
    # parent1 = pdf_out.addBookmark('子目录', 0, parent=parent0)  # 给父添加子目录
    if isinstance(outlines, Destination):
        section = str(outlines.title).split(sep)[0]
        sec_nums = section.split(sec_sep)
        if len(sec_nums) == 1:
            this = pdf_out.addBookmark(outlines.title, pg_id_num_map[outlines.page.idnum] + page_number_offset, parent=parent)  # 添加父目录
        else:
            parent_sec = sec_sep.join(sec_nums[:-1])
            if parent_sec not in parents:
                # warnings.warn(f"不存在父目录：{outlines.title} in {str(parents.keys())}")
                this = pdf_out.addBookmark(outlines.title, pg_id_num_map[outlines.page.idnum] + page_number_offset, parent=parent)  # 添加父目录
            else:
                parent = parents[parent_sec]
                this = pdf_out.addBookmark(outlines.title, pg_id_num_map[outlines.page.idnum] + page_number_offset, parent=parent)  # 添加父目录
        parents[section] = this
        return this
    elif isinstance(outlines, list):
        parent_sub: IndirectObject = None
        parent_dest: Destination = None
        for outline in outlines:
            if isinstance(outline, Destination):
                parent_sub = add_bookmark(pdf_out, outline, parent=parent, page_number_offset=page_number_offset, sep=sep, sec_sep=sec_sep, parents=parents)
            elif isinstance(outline, list):
                assert parent_sub != None, "存在子项时，parent0不应该为None"
                add_bookmark(pdf_out, outline, parent=parent_sub, page_number_offset=page_number_offset)
                parent_sub = None
            else:
                raise Exception(f"未知的类型 {str(type(outline))}")
    else:
        raise Exception(f"未知的类型 {str(type(outline))}")


add_bookmark(pdf_out, outlines, 16)

# 保存pdf
with open(pdfpath + '.pdf', 'wb') as fout:
    pdf_out.write(fout)
