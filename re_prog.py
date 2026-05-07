def f_re():
    import re
    # import utils.rs_db as rs_db
    # from asgiref.sync import sync_to_async
    #
    # f = rs_db.get_run_function
    #
    # if 'db' in param:
    #     p = await sync_to_async(f)("f_get_test", {'d': 128}, execute_type=rs_db.TypeExecuteEnum.ONE_RESULT)
    #     print(p)
    p = {}

    # \"(.+)\"
    # (?:\\.|[^"\n])*

    pattern = re.compile('(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.('
                         '?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)')

    pattern_a = re.compile(
        '\\bdeny \\b(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.('
        '?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)')

    pattern_w = re.compile(r'(\bConnection refused\b)|(\brequest:\b)', re.IGNORECASE)

    pattern_d = re.compile(r'\d{2}/\w+/\d{4}:\d{2}:\d{2}:\d{2}', re.IGNORECASE)
    pattern_c = re.compile(r'\"\w+.+', re.DOTALL)

    d = set()

    # with open('Y:\\Yandex VM\\7-rs\\nginx_access.log') as f:
    #     while True:
    #         content = f.readline()
    #         if re.search(pattern_d, content):
    #             l = re.findall(pattern_c, content)
    #
    #             # l = re.findall(pattern_d, content)
    #             # if l:
    #             #     i = l[0]
    #             #     d_t = datetime.strptime(i, '%d/%b/%Y:%H:%M:%S')
    #             #     d.update(l[:1])
    #
    #
    #         if not content:
    #             break

    with open('Y:\\Yandex VM\\7-rs\\blacklist.conf') as f:
        while True:
            content = f.readline()
            if re.search(pattern_a, content):
                l = re.findall(pattern, content)
                if l:
                    d.update(l[:1])
            if not content:
                break

    with open('Y:\\Yandex VM\\7-rs\\nginx_error.log', 'r') as f:
        while True:
            content = f.readline()
            if re.search(pattern_w, content):
                l = re.findall(pattern, content)
                if l:
                    d.update(l[:1])
            if not content:
                break

    with open('Y:\\Yandex VM\\7-rs\\nginx_.conf', 'w') as f:
        for s in sorted(d):
            f.write(f'deny {s};\n\n')

        f.write(f'allow all;')

    print(d)
    print('Готово!')