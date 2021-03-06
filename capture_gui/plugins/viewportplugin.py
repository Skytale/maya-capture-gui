from capture_gui.vendor.Qt import QtCore, QtWidgets

import capture_gui.plugin
import capture_gui.lib as lib

OBJECT_TYPES = {'Cameras': 'cameras',
                'Control Vertices': 'controlVertices',
                'Deformers': 'deformers',
                'Dimensions': 'dimensions',
                'Dynamic Constraints': 'dynamicConstraints',
                'Dynamics': 'dynamics',
                'Fluids': 'fluids',
                'Follicles': 'follicles',
                'Grid': 'grid',
                'Hair Systems': 'hairSystems',
                'Handles': 'handles',
                'Hulls': 'hulls',
                'Ik Handles': 'ikHandles',
                'ImagePlane': 'imagePlane',
                'Joints': 'joints',
                'Lights': 'lights',
                'Locators': 'locators',
                'Manipulators': 'manipulators',
                'nCloths': 'nCloths',
                'nParticles': 'nParticles',
                'nRigids': 'nRigids',
                'Nurbs Curves': 'nurbsCurves',
                'Nurbs Surfaces': 'nurbsSurfaces',
                'Pivots': 'pivots',
                'Planes': 'planes',
                'Polymeshes': 'polymeshes',
                'Strokes': 'strokes',
                'Subdiv Surfaces': 'subdivSurfaces',
                'Textures': 'textures'}


class ViewportPlugin(capture_gui.plugin.Plugin):
    """Plugin to apply viewport visibilities and settings"""
    id = "Viewport Options"
    label = "Viewport Options"
    section = "config"
    order = 70

    def __init__(self, parent=None):
        super(ViewportPlugin, self).__init__(parent=parent)

        self.show_types_list = list()
        self.plugin_shapes = lib.get_plugin_shapes()

        self.setObjectName(self.label)

        self._layout = QtWidgets.QVBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)
        self.override_viewport = QtWidgets.QCheckBox("Override viewport "
                                                     "settings")
        self.override_viewport.setChecked(True)

        # region Show
        self.show_types_button = QtWidgets.QPushButton("Show")
        self.show_types_button.setFixedWidth(150)
        self.show_types_menu = self._build_show_menu()
        self.show_types_button.setMenu(self.show_types_menu)
        # endregion Show

        # region Checkboxes
        self.high_quality = QtWidgets.QCheckBox()
        self.high_quality.setText("Force Viewport 2.0 + AA")
        # endregion Checkboxes

        self._layout.addWidget(self.override_viewport)
        self._layout.addWidget(self.show_types_button)
        self._layout.addWidget(self.high_quality)

        # signals
        self.high_quality.stateChanged.connect(self.options_changed)
        self.override_viewport.stateChanged.connect(self.options_changed)
        self.override_viewport.stateChanged.connect(self.on_toggle_override)

    def _build_show_menu(self):
        """Build the menu to select which object types are shown in the output.
        
        Returns:
            QtGui.QMenu: The visibilities "show" menu.
            
        """

        menu = QtWidgets.QMenu(self)
        menu.setObjectName("ShowShapesMenu")
        menu.setWindowTitle("Show")
        menu.setFixedWidth(150)
        menu.setTearOffEnabled(True)

        # Show all check
        toggle_all = QtWidgets.QAction(menu, text="All")
        toggle_none = QtWidgets.QAction(menu, text="None")
        menu.addAction(toggle_all)
        menu.addAction(toggle_none)
        menu.addSeparator()

        # add standard object shapes
        for obj_type in OBJECT_TYPES.keys():
            action = QtWidgets.QAction(menu, text=obj_type)
            action.setCheckable(True)

            # Add to menu and list of instances
            menu.addAction(action)
            self.show_types_list.append(action)

        menu.addSeparator()

        # add plugin shapes if any
        plugin_shapes = self.plugin_shapes.keys()
        if plugin_shapes:
            for plugin_shape in plugin_shapes:
                action = QtWidgets.QAction(menu, text=plugin_shape)
                action.setCheckable(True)

                menu.addAction(action)
                self.show_types_list.append(action)

        # connect signals
        toggle_all.triggered.connect(self.toggle_all_visbile)
        toggle_none.triggered.connect(self.toggle_all_hide)

        return menu

    def on_toggle_override(self):
        """Enable or disable show menu when override is checked"""
        state = self.override_viewport.isChecked()
        self.show_types_button.setEnabled(state)
        self.high_quality.setEnabled(state)

    def toggle_all_visbile(self):
        """
        Set all object types off or on depending on the state
        :return: None
        """
        for objecttype in self.show_types_list:
            objecttype.setChecked(True)

    def toggle_all_hide(self):
        """
        Set all object types off or on depending on the state
        :return: None
        """
        for objecttype in self.show_types_list:
            objecttype.setChecked(False)

    def get_show_inputs(self):
        """
        Return checked state of show menu items
        :return: 
        """

        show_inputs = {}
        # get all checked objects
        for action in self.show_types_list:
            action_text = action.text()
            if action_text in OBJECT_TYPES:
                name = OBJECT_TYPES[action_text]
            elif action_text in self.plugin_shapes:
                name = self.plugin_shapes[action_text]
            else:
                continue

            show_inputs[name] = action.isChecked()

        return show_inputs

    def get_inputs(self, as_preset):
        """
        Return the widget options
        :param as_preset: 
        :return: dictionary with all the settings of the widgets 
        """
        inputs = {"high_quality": self.high_quality.isChecked(),
                  "override_viewport_options": self.override_viewport.isChecked()}

        inputs.update(self.get_show_inputs())

        return inputs

    def apply_inputs(self, inputs):
        """
        Apply the settings which can be adjust by the user or presets
        :param inputs: a collection of settings
        :type inputs: dict

        :return: None
        """
        # get input values directly from input given
        override_viewport = inputs.get("override_viewport_options", True)
        high_quality = inputs.get("high_quality", True)

        self.high_quality.setChecked(high_quality)
        self.override_viewport.setChecked(override_viewport)
        self.show_types_button.setEnabled(override_viewport)

        for action in self.show_types_list:
            action.setChecked(inputs.get(action.text(), True))

    def get_outputs(self):
        """
        Retrieve all settings of each available sub widgets
        :return: 
        """

        outputs = dict()

        high_quality = self.high_quality.isChecked()
        override_viewport_options = self.override_viewport.isChecked()

        outputs['viewport2_options'] = dict()
        outputs['viewport_options'] = dict()

        if override_viewport_options and high_quality:
            # force viewport 2.0 and AA
            outputs['viewport_options']['rendererName'] = 'vp2Renderer'
            outputs['viewport2_options']['multiSampleEnable'] = True
            outputs['viewport2_options']['multiSampleCount'] = 8

        # Viewport visibility settings
        if override_viewport_options:
            show_per_type = self.get_show_inputs()
            outputs['viewport_options'].update(show_per_type)
        else:
            # If not override force all to True
            show_per_type = self.get_show_inputs()
            show_per_type = {key: True for key in show_per_type}
            outputs['viewport_options'].update(show_per_type)

        return outputs
