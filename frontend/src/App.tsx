import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { 
  Box, 
  Button, 
  Container, 
  Heading, 
  Text, 
  VStack, 
  HStack, 
  useColorMode, 
  IconButton,
  Flex
} from '@chakra-ui/react';
import { MoonIcon, SunIcon } from '@chakra-ui/icons';
import './styles/App.css';

function App() {
  const { colorMode, toggleColorMode } = useColorMode();

  return (
    <Box minH="100vh" bg={colorMode === 'light' ? 'gray.50' : 'gray.900'}>
      {/* Header */}
      <Box bg={colorMode === 'light' ? 'white' : 'gray.800'} shadow="sm">
        <Container maxW="container.xl">
          <Flex justifyContent="space-between" alignItems="center" py={4}>
            <Heading size="lg" color="teal.500">
              Inventario App
            </Heading>
            <HStack spacing={4}>
              <IconButton
                aria-label="Toggle theme"
                icon={colorMode === 'light' ? <MoonIcon /> : <SunIcon />}
                onClick={toggleColorMode}
                variant="ghost"
              />
            </HStack>
          </Flex>
        </Container>
      </Box>

      {/* Main Content */}
      <Container maxW="container.xl" py={8}>
        <VStack spacing={6}>
          <Box textAlign="center">
            <Heading size="xl" mb={2}>
              Sistema de Inventario
            </Heading>
            <Text color="gray.600" fontSize="lg">
              Modern Flask API + React Frontend with Chakra UI
            </Text>
          </Box>

          <HStack spacing={4} flexWrap="wrap">
            <Button colorScheme="teal" variant="solid" size="lg">
              Agregar Producto
            </Button>
            <Button colorScheme="blue" variant="outline" size="lg">
              Ver Inventario  
            </Button>
            <Button colorScheme="green" variant="ghost" size="lg">
              Punto de Venta
            </Button>
          </HStack>

          <Box w="full">
            <Routes>
              <Route 
                path="/" 
                element={
                  <Box textAlign="center" py={8}>
                    <Heading size="md" mb={4}>Dashboard - Coming Soon</Heading>
                    <Text color="gray.500">
                      El dashboard estará disponible pronto con estadísticas y métricas
                    </Text>
                  </Box>
                } 
              />
              <Route 
                path="/inventory" 
                element={
                  <Box textAlign="center" py={8}>
                    <Heading size="md" mb={4}>Inventario - Coming Soon</Heading>
                    <Text color="gray.500">
                      Gestión completa de productos e inventario
                    </Text>
                  </Box>
                } 
              />
              <Route 
                path="/cash" 
                element={
                  <Box textAlign="center" py={8}>
                    <Heading size="md" mb={4}>Caja - Coming Soon</Heading>
                    <Text color="gray.500">
                      Punto de venta y gestión de transacciones
                    </Text>
                  </Box>
                } 
              />
            </Routes>
          </Box>
        </VStack>
      </Container>
    </Box>
  );
}

export default App;