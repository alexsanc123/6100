tokens = sorted(set(csm_api.get_api_tokens(globals(), cs_username)))

prefix_length = 5
while True:
    prefixes = [i[:prefix_length] for i in tokens]
    if len(prefixes) == len(tokens):
        break

if prefixes:
    plural = "s" if len(tokens) != 1 else ""
    print(
        '<p>You currently have <b>%s</b> API token%s in the system.  Information about your token%s is shown below.  You can also <a href="CURRENT/new-token">generate an additional token</a>.</p>'
        % (len(tokens), plural, plural)
    )
    print("<center>")
    print("<table border='1'>")
    print("<tr><th>Token</th><th>Delete?</th></tr>")
    for p in prefixes:
        print("<tr>")
        print(f"<td><tt>{p}...</tt></td>")
        print(f'<td><a href="CURRENT/delete-token?prefix={p}">Delete</a>')
    print("</table>")
    print("</center>")
    print()
else:
    print(
        '<p>You currently have no API tokens in the system.  You can <a href="CURRENT/new-token">generate a new token</a>.</p>'
    )
