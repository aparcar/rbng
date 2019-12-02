#!/usr/bin/env python3

from jinja2 import Environment, FileSystemLoader
from playhouse.reflection import generate_models
from playhouse.shortcuts import model_to_dict
import json
import peewee as pw
from pathlib import Path

db = pw.PostgresqlDatabase(
    "rbdb", host="localhost", port=5000, user="rb", password="foo"
)
db.connect()

# db.execute_sql("drop view vsources cascade")
db.execute_sql(
    "create or replace view vsources as select s.id as package_id, d.name as distro, s.name, s.suite, s.architecture from sources s join distributions d on s.distribution = d.id"
)

# db.execute_sql("drop view vresults")
db.execute_sql(
    "create or replace view vresults as select * from vsources v join results r using (package_id)"
)

models = generate_models(db, include_views=True)
globals().update(models)


# with db.atomic() as txn:
#    suites = txn.execute_sql("select distinct suite from vsources where distro = 'archlinux'").fetchall()
#    print(suites)


distros = ["coreboot", "opensuse", "openwrt", "debian", "archlinux"]

for distro in distros:
    print(f"rendering { distro }")
    context = {}
    context["distro"] = distro
    context["suites"] = {}

    query = db.execute_sql(
        "SELECT suite, architecture, status, count(*) FROM vresults WHERE distro = %s group by (suite, architecture, status)",
        (context["distro"],),
    )

    states = set()

    for row in query.fetchall():
        suite, arch, status, count = row
        if suite not in context["suites"]:
            context["suites"][suite] = {}
        if arch not in context["suites"][suite]:
            context["suites"][suite][arch] = {}
            context["suites"][suite][arch] = {"total": 0}
        context["suites"][suite][arch][status] = count
        states.add(status)

        context["suites"][suite][arch]["total"] += count

    query = db.execute_sql(
        "select * from vresults where distro = %s and date(build_date) = '2019-11-08'",
        (context["distro"],),
    )

    file_loader = FileSystemLoader(["templates", context["distro"]])
    env = Environment(loader=file_loader)
    env.trim_blocks = True
    env.lstrip_blocks = True
    env.rstrip_blocks = True

    print(states)

    # print(query.fetchall())
    for suite in context["suites"]:
        for arch in context["suites"][suite]:
            for status in states:
                artifacts = (
                    vresults.select()
                    .where(vresults.distro == context["distro"], vresults.architecture == arch, vresults.status == status)
                    .limit(100)
                    .dicts()
                )
                template = env.get_template("artifacts.html")
                output = template.render(**context, suite=suite, artifacts=list(artifacts))
                output_file = Path(f"{context['distro']}/{suite}/{arch}/{status.lower()}.html")
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text(output)

    # print(json.dumps(context, indent="  "))

    template = env.get_template("overview.html")
    output = template.render(**context)

    Path(f"{ context['distro'] }/index.html").write_text(output)
