import plotly.graph_objects as go
import plotly.express as px
import json
from collections import defaultdict
from operator import itemgetter
import sys

COLORS = {
    "file": "#002060",
    "unknown": "#008ed5"
}


def load_reports(report_path):
    objects = {}
    parent_sizes = defaultdict(lambda: 0)

    with open(report_path, "r") as f:
        reports = json.load(f)
        for report in reports:

            task = report['task']
            obj = {
                "id": task['path'],
                "depth": task['depth'],
                "path": task['path'],
                "size": 0,
                "parent": task['blob_id'],
                "mime": None,
            }

            for sub_report in report['reports']:
                if sub_report["__typename__"] == "StatReport":
                    obj['size'] = sub_report['size']
                    parent_sizes[obj['parent']] += obj['size']
                    if sub_report['is_file']:
                        obj['type'] = 'file'
                    else:
                        obj['type'] = 'misc'
                elif sub_report["__typename__"] == "FileMagicReport":
                    obj['mime'] = sub_report['mime_type']
                elif sub_report["__typename__"] == "ChunkReport":
                    chunk_obj = {
                        "id": sub_report['id'],
                        "path": ":".join([task['path'], str(sub_report['start_offset']), str(sub_report['end_offset'])]),
                        "type": sub_report['handler_name'],
                        "mime": sub_report['handler_name'],
                        "size": sub_report['size'],
                        "depth": task['depth'] + 0.5,
                        "parent": obj['id']
                    }
                    parent_sizes[chunk_obj['parent']] += int(chunk_obj['size'])
                    objects[chunk_obj['id']] = chunk_obj
                elif sub_report['__typename__'] == "UnknownChunkReport":
                    chunk_obj = {
                        "id": sub_report['id'],
                        "path": ":".join([task['path'], str(sub_report['start_offset']), str(sub_report['end_offset'])]),
                        "type": "unknown",
                        "mime": "unknown",
                        "size": sub_report['size'],
                        "depth": task['depth'] + 0.5,
                        "parent": obj['id']
                    }
                    parent_sizes[chunk_obj['parent']] += int(chunk_obj['size'])
                    objects[chunk_obj['id']] = chunk_obj
                elif sub_report['__typename__'] == 'HashReport':
                    pass
                #else:
                #    print("UNKNOWN REPORT", sub_report)

                objects[obj['id']] = obj
    return objects, parent_sizes



def process_objects(objects, parent_sizes):
    aggregated_objects = defaultdict(lambda: dict(percent=0, size=0, type="file", count=0))
    simple_objects = []

    for obj in sorted(objects.values(), key=itemgetter('depth')):
        obj['label'] = obj['path'].split('/')[-1]
        obj['color'] = COLORS.get(obj['type'], "#00FFC8")
        obj['text'] = "Type: {}<br>Mime: {}<br>Size: {:.2f} MB<br>{}".format(obj['type'], obj['mime'], obj['size'] / 1024/1024, obj['path'])

        if not obj['parent']:
            obj['percent'] = 100
            simple_objects.append(obj)
            continue

        if obj['type'] == "file":
            parent_size = parent_sizes[obj['parent']]
        else:
            parent_size = objects[obj['parent']]['size']

        if 'percent' not in objects[obj['parent']]:
            print("PERCENT MISSING", obj, objects[obj['parent']])

        parent_percent = objects[obj['parent']]['percent']
        obj['percent'] =  (obj['size'] / parent_size) * parent_percent

        # merge file by mime type, exclude files which has child or mime type is application/octet-stream

        if obj['type'] == 'file' and obj['mime'] != "application/octet-stream" and obj['id'] not in parent_sizes:
            agg_object = aggregated_objects[(obj['parent'], obj['mime'])]
            agg_object['percent'] += obj['percent']
            agg_object['size'] += obj['size']
            agg_object['count'] += 1
            agg_object['mime'] = obj['mime']
            agg_object['id'] = obj['parent'] + "__" + str(obj['mime'])
            agg_object['parent'] = obj['parent']
            agg_object['label'] = "{count} {mime}".format(**agg_object)
            agg_object['color'] = "#3c3c3b"
            agg_object['text'] = "Count: {}<br>Mime: {}<br>Size: {:.2f} MB<br>".format(agg_object['count'], agg_object['mime'], agg_object['size'] / 1024/1024, agg_object['id'])
        elif obj['type'] == "misc":
            # SKIP links & directories
            pass
        else:
            if obj['mime'] == "application/octet-stream":
                obj['color'] = '#dadada'
            simple_objects.append(obj)

    return simple_objects, aggregated_objects

def create_chart(display_objects, chart):
    fig = go.Figure(chart(
        ids=[x['id'] for x in display_objects],
        labels=[x['label'] for x in display_objects],
        parents=[x['parent'] for x in display_objects],
        values=[x['percent'] for x in display_objects],
        hovertext=[x['text'] for x in display_objects],
        marker=dict(
            colors=[x['color'] for x in display_objects],
        ),    
        branchvalues='total'
    ))

    # Update layout for tight margin
    # See https://plotly.com/python/creating-and-updating-figures/
    fig.update_layout(margin = dict(t=40, l=10, r=10, b=10), width=1000, height=1000)

    fig.show()


if __name__ == "__main__":
    objects, parent_sizes = load_reports(sys.argv[1])
    simple_objects, aggregated_objects = process_objects(objects, parent_sizes)
    display_objects = simple_objects + list(aggregated_objects.values())

    if sys.argv[2] == "sunburst":
        chart = go.Sunburst
    else:
        chart = go.Treemap

    create_chart(display_objects, chart)
