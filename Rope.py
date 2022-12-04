from ursina import *

def dot(v1:Vec3, v2:Vec3):
    return sum([a*b for a,b in zip(v1, v2)])

class Node(Entity):
    def __init__(self, mass:float = 1, kinematic:bool = True, visible:bool = False, *args, **kwargs):
        super().__init__(model=Circle(10) if visible else None, color=color.red, scale=0.15, billboard=True, *args, **kwargs)
        self.force_ = Vec3(0,0,0)
        self.velocity = Vec3(0,0,0)
        self.mass = mass
        self.kinematic = kinematic
    
    def update(self):
        if self.kinematic:
            self.force += Vec3(0, -9.81*self.mass, 0)
            self.velocity += (self.force * time.dt) / self.mass
            self.position += self.velocity * time.dt
            self.force = Vec3(0,0,0)
    
    @property
    def force(self):
        return self.force_
    @force.setter
    def force(self, new:Vec3):
        if not self.kinematic:
            return
        self.force_ = new

class Rope(Entity):
    def __init__(self, node_count:int = 12, nodes_visible:bool = False, natural_length:float = 5, stiffness:float = 10, dampening:float = 3, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.natural_length = natural_length
        self.stiffness = stiffness
        self.dampening = dampening
        self.kinematic_ = False

        self.nodes_ = []
        for n in range(0, node_count): #possible list comprehension instead, probably less readble though (node_count,0,-1) (n!=node_count)
            node = Node(parent=self, y = n*(-natural_length/node_count), kinematic = False, mass = 0.5/node_count, visible = nodes_visible) #kinematic: (n!=0)
            self.nodes_.append(node)
        
        self.model = Mesh(mode="line", vertices=[node.position for node in self.nodes_], thickness=5)
    
    def update(self):
        self.model.vertices = [node.position for node in self.nodes_]
        self.model.generate()

        for node1, node2 in zip(self.nodes_, self.nodes_[1:]):
            self.resolve_forces(node1, node2)
    
    def resolve_forces(self, node1:Node, node2:Node):
        if self.kinematic:
            direction = node2.position - node1.position
            total_force = (distance(node1,node2)-self.natural_length/len(self.nodes_))*self.stiffness
            total_force += dot(direction.normalized(),(node2.velocity-node1.velocity))*self.dampening
            node1.force += direction.normalized() * total_force
            node2.force += direction.normalized() * total_force * -1
    
    def apply_force(self, force:Vec3, node:int = 0):
        if self.kinematic:
            self.nodes_[len(self.nodes_)-(1+node)].force += force
    
    def calm_velocities(self):
        for node in self.nodes_:
            node.velocity = Vec3(0,0,0)
    
    @property
    def kinematic(self):
        return self.kinematic_
    @kinematic.setter
    def kinematic(self, new:bool):
        self.kinematic_ = new
        for node in self.nodes_[1:]:
            node.kinematic = self.kinematic


if __name__ == "__main__":
    from ursina.shaders import basic_lighting_shader

    app = Ursina()
    ground = Entity(scale=(1000,1,1000), model="cube", texture="white_cube", texture_scale=(1000,1000), color=rgb(100,100,100))
    rope = Rope(y=10)
    cube = Entity(parent=rope, model="cube", texture="white_cube", color=color.red, scale=0.5, shader=basic_lighting_shader)

    def input(key):
        if key in ["right arrow", "left arrow", "up arrow", "down arrow"]:
            x_dir = int(key == "right arrow") - int(key == "left arrow")
            z_dir = int(key == "up arrow") - int(key == "down arrow")
            rope.apply_force(Vec3(50*x_dir, 0 ,50*z_dir))
        
        if key == "space":
            rope.calm_velocities()
        
        if key == "enter":
            rope.kinematic = not rope.kinematic
    
    def update():
        #"attach" cube
        cube.look_at(cube.position + (rope.nodes_[-2].position-rope.nodes_[-1].position))
        cube.position = rope.nodes_[-1].position

    EditorCamera(y=5)
    app.run()