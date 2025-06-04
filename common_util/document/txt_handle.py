import os


# 整合多个txt为一个
original_path = r'I:\LST_interpolation_result\day_highquality\h24v05\interpolation_failed'
target_path = r'I:\LST_interpolation_result\day_highquality\h24v05'
txts = os.listdir(original_path)
with open(os.path.join(target_path, 'interpolation_failed.txt'), 'a') as f1:
    for txt in txts:
        f1.write('\n%s\n' % os.path.splitext(txt)[0])
        with open(os.path.join(original_path, txt)) as f2:
            f1.writelines(f2.readlines())
