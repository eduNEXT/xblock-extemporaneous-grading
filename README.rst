Extemporaneous Grading XBlock
#############################

|status-badge| |license-badge| |ci-badge|


Purpose
*******

Extemporaneous Grading is an XBlock that allows the course author to set a due
date and a late due date for a set of components. The learner will only be able
to see the content of the components if they are within the established dates.

This XBlock has been created as an open source contribution to the Open
edX platform and has been funded by **Unidigital** project from the Spanish
Government - 2023.


Enabling the XBlock in a course
*******************************

Once the XBlock has been installed in your Open edX installation, you can
enable it in a course from Studio through the **Advanced Settings**.

1. Go to Studio and open the course to which you want to add the XBlock.
2. Go to **Settings** > **Advanced Settings** from the top menu.
3. Search for **Advanced Module List** and add ``"extemporaneous_grading"``
   to the list.
4. Click **Save Changes** button.


Adding a Extemporaneous Grading Component to a course unit
**********************************************************

From Studio, you can add the Extemporaneous Grading Component to a course unit.

1. Click on the **Advanced** button in **Add New Component**.

   .. image:: https://github.com/eduNEXT/xblock-extemporaneous-grading/assets/64033729/d44072d0-d5be-4a64-9fb1-54e97035e720
      :alt: Open Advanced Components

2. Select **Extemporaneous Grading** from the list.

   .. image:: https://github.com/eduNEXT/xblock-extemporaneous-grading/assets/64033729/1f6331bf-4b08-4381-8661-f59673d03e00
      :alt: Select Extemporaneous Grading Component

3. Configure the component as needed.


View from the Learning Management System (CMS)
**********************************************

The **Extemporaneous Grading** component has a set of settings that can be
configured by the course author.

.. image:: https://github.com/eduNEXT/xblock-extemporaneous-grading/assets/64033729/05a94a2b-adaf-433f-83fb-53c0fccfbd22
    :alt: Settings for the Extemporaneous Grading component

The **Extemporaneous Grading** component has the following settings:

- **Due Date**: Allows the course author to set a due date for the component.
- **Due Time**: Allows the course author to set a due time for the component.
  This field and the **Due Date** field are used together. The format for the
  time is "HH:MM".
- **Late Due Date**: Allows the course author to set a late due date for the
  component.
- **Late Due Time**: Allows the course author to set a late due time for the
  component. This field and the **Late Due Date** field are used together. The
  format for the time is "HH:MM".
- **Due Date Explanation Text**: Allows the course author to set the text that
  will be displayed to the learner when the due date has passed.
- **Late Due Date Explanation Text**: Allows the course author to set the text
  that will be displayed to the learner when the late due date has passed.

Here is how the **Extemporaneous Grading** component looks in the
**Author View**:

.. image:: https://github.com/eduNEXT/xblock-extemporaneous-grading/assets/64033729/c4226b8d-853b-44e1-b6e6-6378b8e90cfa
    :alt: Author view for component

When accessing the component by selecting the **VIEW ➔** button, you will see
the list of children components that are part of the Extemporaneous Grading
component.

.. image:: https://github.com/eduNEXT/xblock-extemporaneous-grading/assets/64033729/ee9226b1-784e-40a0-b345-fb71af382492
    :alt: View of the component

Here is an example of a Extemporaneous Grading component with a **Problem**
component as a child:

.. image:: https://github.com/eduNEXT/xblock-extemporaneous-grading/assets/64033729/ccc07701-046c-44c3-90df-1db0c359d2a5
    :alt: Example of a Extemporaneous Grading component with a Problem component as a child


View from the Learning Management System (LMS)
**********************************************

When a learner accesses the component in the course before the due datetime,
they will see the content of the component.

.. image:: https://github.com/eduNEXT/xblock-extemporaneous-grading/assets/64033729/c8caa980-3249-4215-9a6d-49d56ba413bc
    :alt: View of the component in the LMS before the due datetime

When a learner accesses the component in the course after the due datetime,
they will a message indicating that the due datetime has passed. The learner
will be able to see the content if they press the **Accept Late Submission**
button.

.. image:: https://github.com/eduNEXT/xblock-extemporaneous-grading/assets/64033729/bda9c7a8-a6ef-4533-ba93-213643880647
    :alt: View of the component in the LMS after the due datetime

When a learner accesses the component in the course after the late due datetime,
they will a message indicating that the late due datetime has passed and they
will not be able to see the content of the component.

.. image:: https://github.com/eduNEXT/xblock-extemporaneous-grading/assets/64033729/11eca4eb-5a0b-4209-a892-316ca7eace06
    :alt: View of the component in the LMS after the late due datetime


Experimenting with this XBlock in the Workbench
************************************************

`XBlock`_ is the Open edX component architecture for building custom learning
interactive components.

You can see the Extemporaneous Grading component in action in the XBlock
Workbench. Running the Workbench requires having docker running.

.. code::

    git clone git@github.com:eduNEXT/xblock-extemporaneous-grading
    virtualenv venv/
    source venv/bin/activate
    cd xblock-extemporaneous-grading
    make upgrade
    make install
    make dev.run

Once the process is done, you can interact with the Extemporaneous Grading
XBlock in the Workbench by navigating to http://localhost:8000

For details regarding how to deploy this or any other XBlock in the Open edX
platform, see the `installing-the-xblock`_ documentation.

.. _XBlock: https://openedx.org/r/xblock
.. _installing-the-xblock: https://edx.readthedocs.io/projects/xblock-tutorial/en/latest/edx_platform/devstack.html#installing-the-xblock

Getting Help
*************

If you're having trouble, the Open edX community has active discussion forums
available at https://discuss.openedx.org where you can connect with others in
the community.

Also, real-time conversations are always happening on the Open edX community
Slack channel. You can request a `Slack invitation`_, then join the
`community Slack workspace`_.

For anything non-trivial, the best path is to open an `issue`_ in this
repository with as many details about the issue you are facing as you can
provide.

For more information about these options, see the `Getting Help`_ page.

.. _Slack invitation: https://openedx.org/slack
.. _community Slack workspace: https://openedx.slack.com/
.. _issue: https://github.com/eduNEXT/xblock-extemporaneous-grading/issues
.. _Getting Help: https://openedx.org/getting-help


License
*******

The code in this repository is licensed under the AGPL-3.0 unless otherwise
noted.

Please see `LICENSE.txt <LICENSE.txt>`_ for details.


Contributing
************

Contributions are very welcome.

This project is currently accepting all types of contributions, bug fixes,
security fixes, maintenance work, or new features.  However, please make sure
to have a discussion about your new feature idea with the maintainers prior to
beginning development to maximize the chances of your change being accepted.
You can start a conversation by creating a new issue on this repo summarizing
your idea.

Translations
============

This Xblock is initially available in English and Spanish. You can help by
translating this component to other languages. Follow the steps below:

1. Add the new locale in the ``Makefile`` in the ``LOCALES`` variable. eg:
   ``LOCALES = en es_ES fr_FR``.
2. Run ``make extract_translations`` to generate the folder structure for the
   new locale.
3. Add the translations to the ``text.po`` file in the new locale folder.
4. Run ``make compile_translations`` to generate the ``text.mo`` file.
5. Create a pull request with your changes.


Reporting Security Issues
*************************

Please do not report a potential security issue in public. Please email
security@edunext.co.


.. |ci-badge| image:: https://github.com/eduNEXT/xblock-extemporaneous-grading/actions/workflows/ci.yml/badge.svg?branch=main
    :target: https://github.com/eduNEXT/xblock-extemporaneous-grading/actions
    :alt: CI

.. |license-badge| image:: https://img.shields.io/github/license/eduNEXT/xblock-extemporaneous-grading.svg
    :target: https://github.com/eduNEXT/xblock-extemporaneous-grading/blob/main/LICENSE.txt
    :alt: License

.. |status-badge| image:: https://img.shields.io/badge/Status-Maintained-brightgreen
