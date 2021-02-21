#!/usr/bin/env python3

import argparse
import json
import os
import re
import sys


class JobGenerator(object):
    def __init__(self, args):

        self.libreelec_dir = args.libreelec_dir
        self.output_dir = args.output_dir
        self.template_dir = "job-templates"
        self.dashboard_dir = "dashboard-templates"

        if not os.path.exists(self.libreelec_dir):
            print(f"Path to LibreELEC.tv directory is invalid: {self.libreelec_dir}")
            sys.exit()

        if os.path.exists(self.output_dir):
            print(f"output directory already exists: {self.output_dir}")
            sys.exit()

        os.mkdir(self.output_dir)

    def _parse_projects(self, valid_projects=[], invalid_projects=[]):

        projects = []

        for project in os.listdir(os.path.join(self.libreelec_dir, "projects")):

            # skip special add-ons only project
            if (len(invalid_projects) > 0) and project in invalid_projects:
                continue

            if (len(valid_projects) > 0) and project not in valid_projects:
                continue

            definition = {"project": project}

            if os.path.exists(
                os.path.join(self.libreelec_dir, "projects", project, "devices")
            ):

                # assume and project with "devices" folder uses arm arch
                definition["arch"] = "arm"

                definition["devices"] = []
                for device in os.listdir(
                    os.path.join(self.libreelec_dir, "projects", project, "devices")
                ):
                    definition["devices"].append(device)
            else:
                # assume and project without "devices" folder uses x86_64 arch
                definition["arch"] = "x86_64"

            projects.append(definition)

        return projects

    def _write_files(self, output_file, data, project, device, arch):

        data = data.replace(
            "@NAME@", (lambda x, y: x if len(x) > 0 else y)(device, project)
        )
        data = data.replace("@PROJECT@", project)
        data = data.replace("@DEVICE@", device)
        data = data.replace("@ARCH@", arch)

        include_regions = []
        trigger_phrase = (
            trigger_phrase
        ) = f".*jenkins build this for (?i)({project}|all).*"
        if device != "":
            include_regions.append(os.path.join("projects", project, "(?!devices).*"))
            include_regions.append(
                os.path.join("projects", project, "devices", device, ".*")
            )

            trigger_phrase = f".*jenkins build this for (?i)({project}|{device}|all).*"

        data = data.replace("@INCLUDE_REGIONS@", "\\n".join(include_regions))
        data = data.replace("@TRIGGER_PHRASE@", trigger_phrase)

        with open(os.path.join(self.output_dir, output_file), "w") as f:
            f.write(data)

    def _process_template(self, template, projects):

        job_list = []

        template_data = ""
        with open(os.path.join(self.template_dir, template)) as f:
            template_data = f.read()

        for object in projects:
            project = object["project"]
            arch = object["arch"]
            if "devices" in object:
                for device in object["devices"]:
                    job_list.append(device)
                    output_file = "_".join(
                        [device.replace("-", "_"), template.replace(".in", "")]
                    )
                    self._write_files(output_file, template_data, project, device, arch)
            else:
                job_list.append(project)
                output_file = "_".join(
                    [project.replace("-", "_"), template.replace(".in", "")]
                )
                self._write_files(output_file, template_data, project, "", arch)

        return job_list

    def _process_dashboard(self, dashboard, jobs):

        dashboard_data = ""

        with open(os.path.join(self.dashboard_dir, dashboard)) as f:
            dashboard_data = f.read()

        job_list = []
        for job in jobs:
            job_list.append(f"        name('{job}')")

        dashboard_data = dashboard_data.replace("@JOBS@", "\n".join(job_list))

        output_file = dashboard.replace(".in", "")
        with open(os.path.join(self.output_dir, output_file), "w") as f:
            f.write(dashboard_data)

    def _process_images(self):

        projects = self._parse_projects(valid_projects=[], invalid_projects=["ARM"])

        print("Projects for builds:")
        print(json.dumps(projects, indent=4))
        print("")

        # process builds
        template = "builds.groovy.in"
        jobs = self._process_template(template, projects)

        # process dashboard
        dashboard = "builds.groovy.in"
        self._process_dashboard(dashboard, jobs)

    def _process_addon_builds(self):

        projects = self._parse_projects(["ARM", "Generic", "RPi"], invalid_projects=[])

        print("Projects for add-ons:")
        print(json.dumps(projects, indent=4))
        print("")

        # process builds
        template = "addons.groovy.in"
        jobs = self._process_template(template, projects)

        # process dashboard
        dashboard = "addons.groovy.in"
        self._process_dashboard(dashboard, [f"{x}-Add-ons" for x in jobs])

    def Run(self):

        self._process_images()

        self._process_addon_builds()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Generate jenkins dsl builds from templates"
    )

    parser.add_argument(
        "--libreelec-dir", default="LibreELEC.tv", help="Path to LibreELEC.tv folder"
    )

    parser.add_argument("--output-dir", default="output", help="Path to output folder")

    args = parser.parse_args()

    generator = JobGenerator(args)

    generator.Run()
